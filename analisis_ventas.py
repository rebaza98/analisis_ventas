import pandas as pd
import unicodedata
import re
import argparse
import os
import bd  # funciones de base de datos
import helpers as hp



DATE_FORMAT = "%Y-%m-%d"
TOP_N_DEFAULT = 3
LISTAR_ULTIMOS_DEFAULT = 5



# Normaliza texto: mayúsculas, sin tildes, sin espacios extras, solo A-Z0-9 y espacios
def normalizar_texto(s: pd.Series) -> pd.Series:
    def limpiar(x: str) -> str:
        x = x.upper().strip()
        x = re.sub(r"\s+", " ", x)
        x = ''.join(
            c for c in unicodedata.normalize('NFD', x)
            if unicodedata.category(c) != 'Mn'
        )
        if not re.search(r"[A-Z0-9]", x):
            return ""
        return x
    return s.astype(str).apply(limpiar).replace("", pd.NA)

# Ejecuta limpieza de datos y retorna DataFrame limpio
def ejecutar_limpieza(csv_path, permite_cero=False):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error al leer el archivo CSV")
        return pd.DataFrame()  

    try:
        reporte = {"total_inicial": len(df)}
        cols = list(df.columns)

        df = df.dropna(subset=cols)

        df["fecha"] = pd.to_datetime(df["fecha"], format=DATE_FORMAT, errors="coerce")
        df = df.dropna(subset=["fecha"])
        df["fecha"] = df["fecha"].dt.date

        df["producto"] = normalizar_texto(df["producto"])
        df = df.dropna(subset=["producto"])

        df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
        df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")
        df = df.dropna(subset=["cantidad", "precio_unitario"])

        if permite_cero:
            df = df[(df["cantidad"] >= 0) & (df["precio_unitario"] >= 0)]
        else:
            df = df[(df["cantidad"] > 0) & (df["precio_unitario"] > 0)]

        df["total"] = hp.calcular_total_serie(df["cantidad"], df["precio_unitario"])

        print(df.head().to_string(index=False))

        eliminadas_total = reporte["total_inicial"] - len(df)
        print("\n=== RESUMEN FINAL ===")
        print("Filas iniciales:", reporte["total_inicial"])
        print("Filas finales:  ", len(df))
        print("Eliminadas total:", eliminadas_total)

        return df
    except Exception as e:
        print(f"Error durante la limpieza de datos: {e}")
        return pd.DataFrame()

def calcular_metricas(df: pd.DataFrame) -> dict:
    """
    Calcula:
      - ranking_cantidad: producto vs. total_cantidad
      - ranking_facturacion: producto vs. total_facturacion
      - facturacion_mensual: mes (YYYY-MM) vs. facturacion_total
      - producto_top_cantidad: primer elemento del ranking_cantidad
      - producto_top_facturacion: primer elemento del ranking_facturacion
    Retorna {} si ocurre algún problema.
    """
    try:
        requeridas = {"fecha", "producto", "cantidad", "precio_unitario", "total"}
        faltan = requeridas - set(df.columns)
        if faltan:
            print(f"Error: faltan columnas requeridas: {', '.join(sorted(faltan))}")
            return {}

        #Producto más vendido por cantidad
        ranking_cantidad = (
            df.groupby("producto", as_index=False)["cantidad"]
              .sum()
              .rename(columns={"cantidad": "total_cantidad"})
              .sort_values("total_cantidad", ascending=False)
        )

        #Producto con mayor facturación total
        ranking_facturacion = (
            df.groupby("producto", as_index=False)["total"]
              .sum()
              .rename(columns={"total": "total_facturacion"})
              .sort_values("total_facturacion", ascending=False)
        )

        #Facturación total por mes (YYYY-MM)
        tmp = df.copy()
        tmp["mes"] = pd.to_datetime(tmp["fecha"]).dt.to_period("M").astype(str)
        facturacion_mensual = (
            tmp.groupby("mes", as_index=False)["total"]
               .sum()
               .rename(columns={"total": "facturacion_total"})
               .sort_values("mes")
        )

        producto_top_cantidad = (
            ranking_cantidad.iloc[0].to_dict() if not ranking_cantidad.empty else None
        )
        producto_top_facturacion = (
            ranking_facturacion.iloc[0].to_dict() if not ranking_facturacion.empty else None
        )

        return {
            "ranking_cantidad": ranking_cantidad,
            "ranking_facturacion": ranking_facturacion,
            "facturacion_mensual": facturacion_mensual,
            "producto_top_cantidad": producto_top_cantidad,
            "producto_top_facturacion": producto_top_facturacion,
        }
    except Exception as e:
        print(f"Error durante el cálculo del análisis: {e}")
        return {}

def imprimir_analisis(res: dict) -> None:
    try:
        if not res:
            print("No se pudo calcular el análisis.")
            return

        print("\n=== ANÁLISIS ===")
        top_c = res.get("producto_top_cantidad")
        if top_c:
            print(f"Producto más vendido (cantidad): {top_c['producto']} -> {int(top_c['total_cantidad'])}")

        top_f = res.get("producto_top_facturacion")
        if top_f:
            print(f"Producto con mayor facturación: {top_f['producto']} -> {float(top_f['total_facturacion']):.2f}")

        print("\nFacturación total por mes:")
        fm = res.get("facturacion_mensual")
        if fm is not None and not fm.empty:
            print(fm.to_string(index=False))
        else:
            print("(sin datos)")
    except Exception as e:
        print(f"Error al imprimir el análisis: {e}")


if __name__ == "__main__":
    #Agrega parametros de línea de comandos    
    parser = argparse.ArgumentParser(description="Limpieza de dataset de ventas")
    parser.add_argument("--csv", help="Ruta del archivo CSV de ventas (por defecto: ventas.csv)")
    parser.add_argument("--permite_cero", action="store_true",
                        help="Permite valores cero en cantidad o precio")
    parser.add_argument("--persistencia", action="store_true",
                    help="Lista los últimos análisis guardados (id, ts y preview Top 3)")
    parser.add_argument("--top", nargs="?", const=-1, type=int,
                    help="Muestra el Top 3 del análisis por id; si no indicas id, usa el último")

    args = parser.parse_args()
    if args.persistencia:
        filas = bd.listar_ultimos(limit=LISTAR_ULTIMOS_DEFAULT, n_preview=TOP_N_DEFAULT)
        if not filas:
            print("No hay análisis guardados.")
        else:
            print(f"=== ÚLTIMOS {LISTAR_ULTIMOS_DEFAULT} ANÁLISIS ===")
            for fila in filas:
                analisis_id = fila["id"]
                ts = fila["ts"] or ""
                print(f"- id={analisis_id} ts={ts}")
                preview = fila.get("top_preview", [])
                hp.imprimir_preview_top(preview)
        raise SystemExit(0)

    if args.top is not None:
        if args.top == -1:
            top = bd.leer_topN_ultimo_cantidad(N=TOP_N_DEFAULT)
            titulo = "último análisis"
        else:
            top = bd.leer_topN_por_id(analisis_id=args.top, N=TOP_N_DEFAULT)
            titulo = f"análisis id={args.top}"

        if not top:
            print("No hay análisis previos o el id indicado no existe.")
        else:
            print(f"=== TOP {TOP_N_DEFAULT} — {titulo} ===")
            for i, fila in enumerate(top, start=1):
                producto = fila.get("producto")
                valor = fila.get("valor")
                valor_formateado = hp.a_entero_si_corresponde(valor)
                print(f"{i}. {producto}: {valor_formateado}")
        raise SystemExit(0)



    modo = []

    try:
        if args.csv:
            csv_file = args.csv
            modo.append("CSV")
        else:
            csv_file = "ventas.csv"
            if not os.path.exists(csv_file):
                raise FileNotFoundError(
                    "No se pasó --csv y no existe ventas.csv en la carpeta actual."
                )

        permite_cero = args.permite_cero
        if args.permite_cero:
            modo.append("PERMITE_CERO")
        if not modo:
            modo = ["DEFAULT"]

        print(f"\n[MODO {','.join(modo)}] archivo={csv_file} permite_cero={permite_cero}\n")

        df = ejecutar_limpieza(csv_file, permite_cero=permite_cero)

        if df.empty:
            print("No se pudo generar resultados (dataframe vacío).")
        else:
            res = calcular_metricas(df)
            imprimir_analisis(res)
            aid = bd.guardar_analisis_q_json(res)  #GUARDA EL RANKING DE MAS VENDIDOS
            fm = res.get("facturacion_mensual")
            hp.generar_grafico_facturacion(fm, ruta_salida="grafico.png")
            print(f"Análisis guardado (id={aid})." if aid else "No se pudo guardar el análisis.")

    except Exception as e:
        print(f"Hubo un problema al procesar: {e}")
