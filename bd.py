# bd.py
import sqlite3
import json
from typing import List, Dict, Any, Optional
import pandas as pd

DB_PATH = "analisis_ventas.sqlite"

def _conectar_db(ruta_db: Optional[str] = None):
    return sqlite3.connect(ruta_db or DB_PATH)

def iniciar_db(ruta_db: Optional[str] = None) -> bool:
    try:
        con = _conectar_db(ruta_db)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analisis (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                ts   TEXT NOT NULL DEFAULT (datetime('now')),
                q_json TEXT
            );
        """)
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error iniciando DB: {e}")
        return False

def _ranking_completo_cantidad(ranking_cantidad: pd.DataFrame) -> List[Dict[str, Any]]:
    
    if ranking_cantidad is None or ranking_cantidad.empty:
        return []
    ordenado = ranking_cantidad.sort_values(
        ["total_cantidad", "producto"], ascending=[False, True]
    )
    salida: List[Dict[str, Any]] = []
    for _, fila in ordenado.iterrows():
        salida.append({
            "producto": fila["producto"],
            "valor": float(fila["total_cantidad"])
        })
    return salida

def guardar_analisis_q_json(res: Dict[str, Any], ruta_db: Optional[str] = None) -> int:
    
    try:
        if not iniciar_db(ruta_db):
            return 0
        arreglo = _ranking_completo_cantidad(res.get("ranking_cantidad"))
        con = _conectar_db(ruta_db)
        cur = con.cursor()
        cur.execute("INSERT INTO analisis (q_json) VALUES (?);", (json.dumps(arreglo),))
        con.commit()
        analisis_id = cur.lastrowid
        con.close()
        return analisis_id
    except Exception as e:
        print(f"Error guardando análisis: {e}")
        return 0

def listar_ultimos(limit: int = 5, n_preview: int = 3, ruta_db: Optional[str] = None) -> List[Dict[str, Any]]:
    
    try:
        if not iniciar_db(ruta_db):
            return []
        con = _conectar_db(ruta_db)
        cur = con.cursor()
        cur.execute("SELECT id, ts, q_json FROM analisis ORDER BY id DESC LIMIT ?;", (limit,))
        filas = cur.fetchall()
        con.close()

        salida: List[Dict[str, Any]] = []
        for analisis_id, ts, qjson in filas:
            try:
                arr = json.loads(qjson) if qjson else []
            except Exception:
                arr = []
            preview = []
            for elem in arr[:n_preview]:
                producto = elem.get("producto")
                valor = elem.get("valor")
                preview.append((producto, valor))
            salida.append({
                "id": analisis_id,
                "ts": ts,
                "top_preview": preview
            })
        return salida
    except Exception as e:
        print(f"Error listando análisis: {e}")
        return []

def leer_topN_ultimo_cantidad(N: int = 3, ruta_db: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        if not iniciar_db(ruta_db):
            return []
        con = _conectar_db(ruta_db)
        cur = con.cursor()
        cur.execute("SELECT q_json FROM analisis ORDER BY id DESC LIMIT 1;")
        fila = cur.fetchone()
        con.close()
        if not fila or fila[0] is None:
            return []
        arr = json.loads(fila[0])
        return arr[:N]
    except Exception as e:
        print(f"Error leyendo Top N: {e}")
        return []

def leer_topN_por_id(analisis_id: int, N: int = 3, ruta_db: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        if not iniciar_db(ruta_db):
            return []
        con = _conectar_db(ruta_db)
        cur = con.cursor()
        cur.execute("SELECT q_json FROM analisis WHERE id = ?;", (analisis_id,))
        fila = cur.fetchone()
        con.close()
        if not fila or fila[0] is None:
            return []
        arr = json.loads(fila[0])
        return arr[:N]
    except Exception as e:
        print(f"Error leyendo Top N por id: {e}")
        return []
