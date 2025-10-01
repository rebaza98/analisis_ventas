import pandas as pd
from pandas.testing import assert_series_equal
import helpers as hp

def test_total_serie_basico():
    cant = pd.Series([1, 2, 3])
    prec = pd.Series([10.0, 0.5, 4])
    esperado = pd.Series([10.0, 1.0, 12.0], dtype=float)
    resultado = hp.calcular_total_serie(cant, prec)
    assert_series_equal(resultado, esperado, check_names=False)

def test_total_serie_coercion_y_nulos():
    cant = pd.Series(["2", "x", None, 4])
    prec = pd.Series(["3.5", 5, 7, "y"])
    # "x", None, "y" -> se convierten en 0.0
    esperado = pd.Series([7.0, 0.0, 0.0, 0.0], dtype=float)
    resultado = hp.calcular_total_serie(cant, prec)
    assert_series_equal(resultado, esperado, check_names=False)

def test_total_serie_ceros_y_negativos():
    cant = pd.Series([0, -2, 3])
    prec = pd.Series([10, 4, -1])
    esperado = pd.Series([0.0, -8.0, -3.0], dtype=float)
    resultado = hp.calcular_total_serie(cant, prec)
    assert_series_equal(resultado, esperado, check_names=False)
