from app.services.excel_import import REQUIRED_COLUMNS, event_hash


def test_required_columns_contract():
    assert REQUIRED_COLUMNS == ["FECHA", "LINEA", "TURNO", "EQUIPO", "DAÑO", "RAZON", "TIEMPO", "FRECUENCIA", "AÑO", "MES"]


def test_event_hash_is_stable():
    a = event_hash(["2026-01-01", "Linea 1", "", "Bomba", "Fuga", "Sello", 10, 1])
    b = event_hash(["2026-01-01", "LINEA 1", "", "bomba", "Fuga", "Sello", 10, 1])
    assert a == b
