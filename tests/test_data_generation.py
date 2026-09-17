import pandas as pd

from generar_datos import REFERENCE_DATE, build_datasets


def test_generated_relations_are_consistent():
    datasets = build_datasets()
    clients = datasets["clientes.csv"]
    invoices = datasets["facturas_emitidas.csv"]

    assert len(clients) == 400
    assert set(invoices["id_cliente"]).issubset(set(clients["id_cliente"]))
    assert invoices["id_factura"].is_unique
    assert (invoices["importe"] > 0).all()


def test_overdue_invoices_are_past_due_and_unpaid():
    invoices = build_datasets()["facturas_emitidas.csv"]
    overdue = invoices[invoices["estado"] == "vencida"]

    assert not overdue.empty
    assert (pd.to_datetime(overdue["fecha_vencimiento"]) < REFERENCE_DATE).all()
    assert overdue["fecha_pago_real"].isna().all()


def test_balance_sheet_balances():
    balance = build_datasets()["balance.csv"]
    assets = balance.loc[balance["tipo"] == "activo", "importe"].sum()
    liabilities = balance.loc[balance["tipo"] == "pasivo", "importe"].sum()
    equity = balance.loc[balance["tipo"] == "patrimonio", "importe"].sum()

    assert assets == liabilities + equity


def test_generation_is_reproducible():
    first = build_datasets()["facturas_emitidas.csv"]
    second = build_datasets()["facturas_emitidas.csv"]

    pd.testing.assert_frame_equal(first, second)
