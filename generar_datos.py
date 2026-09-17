"""Genera datos sintéticos reproducibles para una empresa de servicios B2B."""

from __future__ import annotations

import os
import random

import numpy as np
import pandas as pd


SEED = 2026
FISCAL_YEAR = 2026
REFERENCE_DATE = pd.Timestamp("2026-08-31")
NUM_CLIENTS = 400
DATA_DIR = "data"
EXCEL_DIR = "datos_informe_manual"

random.seed(SEED)
np.random.seed(SEED)

BUSINESS_UNITS = (
    {"name": "Consultoría", "capacity": 120, "active": 108, "fee": 2_400.0},
    {"name": "Servicios Gestionados", "capacity": 100, "active": 91, "fee": 1_850.0},
    {"name": "Datos y Analítica", "capacity": 80, "active": 72, "fee": 3_200.0},
    {"name": "Soporte Empresarial", "capacity": 70, "active": 61, "fee": 1_250.0},
    {"name": "Formación", "capacity": 60, "active": 49, "fee": 900.0},
)


def build_clients() -> pd.DataFrame:
    rows = []
    segments = ("Pyme", "Mid-market", "Enterprise")
    for index in range(1, NUM_CLIENTS + 1):
        unit = BUSINESS_UNITS[(index - 1) % len(BUSINESS_UNITS)]
        rows.append(
            {
                "id_cliente": f"CLI-{index:04d}",
                "nombre": f"Cliente B2B {index:04d}",
                "email": f"finanzas{index:04d}@example.com",
                "telefono": f"+34 910 {index:06d}",
                "unidad": unit["name"],
                "referencia": f"CTR-{FISCAL_YEAR}-{index:04d}",
                "segmento": segments[index % len(segments)],
                "fecha_alta": pd.Timestamp("2023-01-01")
                + pd.Timedelta(days=random.randint(0, 1_200)),
                "cuota_mensual": round(unit["fee"] * np.random.uniform(0.85, 1.20), 2),
            }
        )
    return pd.DataFrame(rows)


def build_invoices(clients: pd.DataFrame) -> pd.DataFrame:
    delayed_ids = set(np.random.choice(clients["id_cliente"], 35, replace=False))
    default_ids = set(np.random.choice(sorted(delayed_ids), 10, replace=False))
    rows = []
    sequence = 1

    for month in range(1, REFERENCE_DATE.month + 1):
        issue_date = pd.Timestamp(FISCAL_YEAR, month, 1)
        due_date = issue_date + pd.Timedelta(days=30)
        for client in clients.itertuples(index=False):
            payment_date = issue_date + pd.Timedelta(days=random.randint(12, 28))
            status = "pagada"

            if client.id_cliente in default_ids and month >= 6:
                payment_date = pd.NaT
                status = "vencida" if due_date < REFERENCE_DATE else "pendiente"
            elif client.id_cliente in delayed_ids and random.random() < 0.30:
                payment_date = due_date + pd.Timedelta(days=random.randint(5, 35))
                if payment_date > REFERENCE_DATE:
                    payment_date = pd.NaT
                    status = "vencida" if due_date < REFERENCE_DATE else "pendiente"

            rows.append(
                {
                    "id_factura": f"FAC-{FISCAL_YEAR}-{sequence:06d}",
                    "id_cliente": client.id_cliente,
                    "unidad": client.unidad,
                    "concepto": f"Servicio mensual {issue_date:%m/%Y}",
                    "importe": client.cuota_mensual,
                    "fecha_emision": issue_date,
                    "fecha_vencimiento": due_date,
                    "estado": status,
                    "fecha_pago_real": payment_date,
                }
            )
            sequence += 1
    return pd.DataFrame(rows)


def build_datasets() -> dict[str, pd.DataFrame]:
    # Reiniciar las semillas permite regenerar exactamente los mismos datos
    # incluso si la función se invoca varias veces en el mismo proceso.
    random.seed(SEED)
    np.random.seed(SEED)
    clients = build_clients()
    invoices = build_invoices(clients)
    utilization = pd.DataFrame(
        {
            "unidad": [unit["name"] for unit in BUSINESS_UNITS],
            "capacidad": [unit["capacity"] for unit in BUSINESS_UNITS],
            "utilizacion_actual": [unit["active"] for unit in BUSINESS_UNITS],
            "precio_medio": [unit["fee"] for unit in BUSINESS_UNITS],
        }
    )
    assets = pd.DataFrame(
        [
            ("ACT-01", "Plataforma tecnológica", "Software", 480_000.0, 160_000.0, 320_000.0, 5, "2024-01-01"),
            ("ACT-02", "Equipos informáticos", "Hardware", 260_000.0, 104_000.0, 156_000.0, 5, "2024-01-01"),
            ("ACT-03", "Mobiliario y oficinas", "Instalaciones", 350_000.0, 87_500.0, 262_500.0, 10, "2023-07-01"),
            ("ACT-04", "Infraestructura de datos", "Hardware", 300_000.0, 75_000.0, 225_000.0, 5, "2025-01-01"),
            ("ACT-05", "Vehículos comerciales", "Transporte", 180_000.0, 54_000.0, 126_000.0, 6, "2024-03-01"),
        ],
        columns=("id_activo", "descripcion", "categoria", "valor_adquisicion", "amortizacion_acumulada", "valor_neto", "vida_util_anos", "fecha_adquisicion"),
    )
    debt = pd.DataFrame(
        [
            ("PRCLI-01", "Banco Demo", "Financiación tecnológica", 420_000.0, 12_800.0, 3.4, "2029-12-31"),
            ("PRCLI-02", "Banco Demo", "Circulante", 250_000.0, 8_200.0, 4.1, "2028-06-30"),
            ("PRCLI-03", "Entidad Simulada", "Equipamiento", 160_000.0, 5_500.0, 3.7, "2029-03-31"),
        ],
        columns=("id_prestamo", "entidad", "tipo", "capital_pendiente", "cuota_mensual", "tipo_interes", "fecha_vencimiento"),
    )

    return {
        "clientes.csv": clients,
        "facturas_emitidas.csv": invoices,
        "utilizacion.csv": utilization,
        "activos_fijos.csv": assets,
        "deuda_bancaria.csv": debt,
        "gastos_fijos.csv": pd.DataFrame(
            [("Personal", "RRHH", 185_000.0, "mensual"), ("Tecnología", "Sistemas", 42_000.0, "mensual"), ("Oficinas", "Operaciones", 28_000.0, "mensual")],
            columns=("concepto", "categoria", "importe_mensual", "periodicidad"),
        ),
        "kpis.csv": pd.DataFrame(
            [("Utilización media", 88.6, 90.0, "%"), ("Tasa de morosidad", 3.8, 2.5, "%"), ("DSO", 39.0, 35.0, "días"), ("EBITDA", 1_280_000.0, 1_200_000.0, "€")],
            columns=("nombre", "valor", "objetivo", "unidad"),
        ),
        "mantenimientos.csv": pd.DataFrame(
            [("M-01", "Infraestructura de datos", "Preventivo", "Revisión técnica", "2026-10-15", 3_500.0, "Proveedor Demo")],
            columns=("id", "activo", "tipo", "descripcion", "proximo_mantenimiento", "coste_estimado", "proveedor"),
        ),
        "pagos_pendientes.csv": pd.DataFrame(
            [("P-01", "Proveedor Cloud", "Servicios cloud", 26_500.0, "2026-09-25", "Alta"), ("P-02", "Proveedor Oficina", "Arrendamiento", 28_000.0, "2026-09-30", "Media")],
            columns=("id", "proveedor", "concepto", "importe", "fecha_vencimiento", "prioridad"),
        ),
        "obligaciones_fiscales.csv": pd.DataFrame(
            [("303", "IVA 3T", "3T", "2026-10-20", "pendiente", 76_500.0)],
            columns=("modelo", "concepto", "periodo", "fecha_limite", "estado", "importe_estimado"),
        ),
        "posicion_caja.csv": pd.DataFrame(
            [("Banco Demo", "ES00-DEMO-0001", "Corriente", 540_000.0), ("Entidad Simulada", "ES00-DEMO-0002", "Corriente", 215_000.0)],
            columns=("banco", "cuenta", "tipo", "saldo"),
        ),
        "balance.csv": pd.DataFrame(
            [("Activo corriente", "activo", 2_400_000.0), ("Activo no corriente", "activo", 1_850_000.0), ("Pasivo", "pasivo", 1_620_000.0), ("Patrimonio neto", "patrimonio", 2_630_000.0)],
            columns=("cuenta", "tipo", "importe"),
        ),
        "cuenta_resultados.csv": pd.DataFrame(
            [("Ventas", "ingreso", 5_800_000.0), ("Costes de personal", "gasto", 2_150_000.0), ("Otros gastos operativos", "gasto", 1_620_000.0)],
            columns=("concepto", "tipo", "importe"),
        ),
        "iva_repercutido.csv": pd.DataFrame([("Servicios B2B", 4_250_000.0, 21.0, 892_500.0)], columns=("concepto", "base", "tipo", "cuota")),
        "iva_soportado.csv": pd.DataFrame([("Compras y servicios", 1_650_000.0, 21.0, 346_500.0)], columns=("concepto", "base", "tipo", "cuota")),
        "desviaciones.csv": pd.DataFrame(
            [("Ventas", 5_500_000.0, 5_800_000.0), ("Gastos operativos", 1_550_000.0, 1_620_000.0)],
            columns=("concepto", "presupuesto", "real"),
        ),
    }


def export_datasets(datasets: dict[str, pd.DataFrame]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(EXCEL_DIR, exist_ok=True)
    for filename, dataframe in datasets.items():
        dataframe.to_csv(os.path.join(DATA_DIR, filename), index=False, sep=",", decimal=".", date_format="%Y-%m-%d", encoding="utf-8")
        dataframe.to_csv(os.path.join(EXCEL_DIR, filename), index=False, sep=";", decimal=",", date_format="%d/%m/%Y", encoding="utf-8-sig")


if __name__ == "__main__":
    generated = build_datasets()
    export_datasets(generated)
    print(f"Generados {len(generated)} archivos reproducibles con semilla {SEED}.")
