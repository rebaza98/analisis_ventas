# Análisis de Ventas

Proyecto de consola en **Python** que:

1) **Limpia** un dataset de ventas (`ventas.csv`)  
2) Calcula **métricas básicas**  
3) **Persiste** el ranking de “más vendidos” en **SQLite**  
4) Genera un **gráfico** de facturación mensual (`grafico.png`)  
5) Incluye **tests con pytest** para la función que calcula la columna `total` (versión vectorizada).

---

## Requisitos

- **Python 3.12** (recomendado)
- Pip y virtualenv

Instalación rápida:

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows (PowerShell)
# .\venv\Scripts\Activate.ps1

python -m pip install -U pip
pip install -r requirements.txt
```

> El proyecto usa `pandas`, `matplotlib` y `pytest`.

---

## Datos de entrada

Archivo CSV con columnas:
- `fecha` — formato **YYYY-MM-DD**
- `producto` — texto
- `cantidad` — numérico
- `precio_unitario` — numérico

Ejemplo (`ventas.csv`):
```csv
fecha,producto,cantidad,precio_unitario
2025-09-01,Teclado,2,45.50
2025-09-02,Mouse,1,30
2025-09-02,Teclado,1,45.50
```

---

## Limpieza de datos (qué hace)

- Elimina filas con **nulos** en columnas presentes.
- Convierte `fecha` a **YYYY-MM-DD** (descarta inválidas).
- **Normaliza** `producto`: mayúsculas, sin tildes, espacios comprimidos; si no hay letras/números se descarta.
- Convierte `cantidad` y `precio_unitario` a numérico (descarta no convertibles).
- Reglas de negocio:
  - Por defecto, **no** permite ceros o negativos.
  - Con `--permite_cero` permite **0** (pero no negativos).
- Calcula `total` usando la función vectorizada `helpers.calcular_total_serie`.

---

## Uso (CLI)

### Ejecutar análisis (lee CSV, limpia, calcula y guarda)
#### Usa ventas.csv si existe en la carpeta actual
```bash
python analisis_ventas.py
```
#### O indicando el archivo opcional
```bash
python analisis_ventas.py --csv ventas.csv
```

#### Permitir ceros en cantidad / precio_unitario
```bash
python analisis_ventas.py --csv ventas.csv --permite_cero

```

Al finalizar:
- Muestra en consola el análisis (productos top y facturación mensual).
- Genera **`grafico.png`** (barras 2 colores, totales encima).
- Persiste el **ranking de “más vendidos”** en **`analisis_ventas.sqlite`**.

### Consultar persistencia Ejecutar con --persistencia (no lee CSV)
#### Lista los últimos 5 análisis (id, timestamp, y preview Top 3)
```bash
python analisis_ventas.py --persistencia
```

### Mostrar el Top 3 guardado Ejecutar con --top (no lee CSV)
#### Del último análisis
```bash
python analisis_ventas.py --top
```
#### De un análisis específico (por id)
```bash
python analisis_ventas.py --top 7
```

> Nota: `--persistencia` y `--top` son **modos de solo lectura**.  
> Si los combinas con `--csv`, se **ignora** el CSV.

---

## Persistencia (SQLite)

Archivo: **`analisis_ventas.sqlite`**

Esquema mínimo:
```sql
CREATE TABLE IF NOT EXISTS analisis (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  ts     TEXT NOT NULL DEFAULT (datetime('now')), -- UTC
  q_json TEXT                                    -- JSON con ranking completo
);
```

`q_json` guarda una lista tipo:
```json
[{"producto": "TECLADO", "valor": 20.0}, {"producto": "MOUSE", "valor": 15.0}]
```

### Consulta SQL pedida (Top 3 del último análisis)
Archivo: **`top3_productos.sql`**
```sql
SELECT
  json_extract(value, '$.producto') AS producto,
  json_extract(value, '$.valor')    AS total_cantidad
FROM analisis, json_each(q_json)
WHERE id = (SELECT id FROM analisis ORDER BY id DESC LIMIT 1)
ORDER BY total_cantidad DESC, producto ASC
LIMIT 3;
```
Ejecutar con `sqlite3`:
```bash
sqlite3 analisis_ventas.sqlite < top3_productos.sql
```

---

## Gráfico

Se genera **`grafico.png`** en la carpeta donde se ejecuta el script.

---

## Tests (pytest)

Se valida la **función de cálculo del total** usada en el pipeline (`helpers.calcular_total_serie`).

Ejecución:
```bash
pytest -q
```

> Para evitar problemas de importación, se incluye `pytest.ini` con:
> ```ini
> [pytest]
> pythonpath = .
> ```

---

## Estructura del repo

```
.
├── analisis_ventas.py        # Script principal (CLI)
├── bd.py                     # Persistencia SQLite
├── helpers.py                # Utilidades (gráfico, formateo, cálculo total)
├── requirements.txt
├── top3_productos.sql
├── pytest.ini                # (pythonpath=. para pytest)
├── tests/
│   └── test_total_serie.py   # Tests de cálculo de total (vectorizado)
└── README.md
```



## Licencia

Este proyecto se distribuye con fines de evaluación técnica.  
Puedes adaptarlo libremente para tu propio uso.
