from typing import Iterable, Tuple, List, Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def a_entero_si_corresponde(x):
    try:
        valor = float(x)
    except (TypeError, ValueError):
        return x
    return int(valor) if valor.is_integer() else x

def imprimir_preview_top(preview: Iterable[Tuple[Optional[str], Any]]) -> None:
    for i, par in enumerate(preview, start=1):
        if not isinstance(par, (list, tuple)) or len(par) != 2:
            continue
        producto, valor = par
        if producto is None:
            continue
        valor_formateado = a_entero_si_corresponde(valor)
        print(f"   {i}. {producto}: {valor_formateado}")

def imprimir_top_diccionarios(items: List[Dict[str, Any]]) -> None:
    for i, fila in enumerate(items, start=1):
        producto = fila.get("producto")
        valor = fila.get("valor")
        valor_formateado = a_entero_si_corresponde(valor)
        print(f"{i}. {producto}: {valor_formateado}")

def generar_grafico_facturacion(
    facturacion_mensual: pd.DataFrame,
    ruta_salida: str = "grafico.png",
    colores: tuple[str, str] = ("#4C78A8", "#F58518"),
) -> Optional[str]:
    try:
        if facturacion_mensual is None or facturacion_mensual.empty:
            print("No se generó gráfico: no hay datos de facturación mensual.")
            return None

        esperadas = {"mes", "facturacion_total"}
        if not esperadas.issubset(set(facturacion_mensual.columns)):
            print("No se generó gráfico: columnas faltantes en 'facturacion_mensual'.")
            return None

        df_plot = facturacion_mensual.copy().sort_values("mes")
        etiquetas = df_plot["mes"].tolist()
        valores = df_plot["facturacion_total"].astype(float).tolist()
        posiciones = list(range(len(etiquetas)))
        colores_barras = [colores[i % 2] for i in range(len(valores))]

        fig, ax = plt.subplots()
        ax.bar(posiciones, valores, color=colores_barras, edgecolor="black")

        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}"))
        ax.set_title("Facturación total por mes")
        ax.set_xlabel("Mes (YYYY-MM)")
        ax.set_ylabel("Facturación total")

        ax.set_xticks(posiciones)
        ax.set_xticklabels(etiquetas, rotation=45, ha="right")

        for x, y in zip(posiciones, valores):
            etiqueta = f"{y:,.0f}"
            ax.text(x, y, etiqueta, ha="center", va="bottom", fontsize=9)

        fig.tight_layout()
        fig.savefig(ruta_salida, dpi=150)
        plt.close(fig)

        print(f"Gráfico guardado en: {ruta_salida}")
        return ruta_salida
    except Exception as e:
        print(f"Error al generar el gráfico: {e}")
        return None


def calcular_total(cantidad, precio_unitario):
  
    try:
        return float(cantidad) * float(precio_unitario)
    except Exception:
        return 0.0

def calcular_total_serie(cantidades: pd.Series, precios: pd.Series) -> pd.Series:
    # Convertir a numérico y forzar float para que el resultado sea float64 siempre
    c = pd.to_numeric(cantidades, errors="coerce").astype(float).fillna(0.0)
    p = pd.to_numeric(precios,    errors="coerce").astype(float).fillna(0.0)
    return c * p