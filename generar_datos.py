import pandas as pd
import numpy as np
import random
import os
from datetime import date, timedelta, datetime

# --- 1. CONFIGURACIÓN ---
random.seed(2025)
np.random.seed(2025)

NUM_ESTUDIANTES = 1000
ANIO_FISCAL = 2025

# Carpetas de Salida
DIR_AGENTES = "data" # FORMATO MÁQUINA (UTF-8, sep=",", dec=".")
DIR_EXCEL = "datos_informe_manual"     # FORMATO HUMANO ES (UTF-8-SIG, sep=";", dec=",")

for d in [DIR_AGENTES, DIR_EXCEL]:
    if not os.path.exists(d):
        os.makedirs(d)

TIPOS_RESIDENCIA = {
    'Premium': {'cantidad': 5, 'precio': 1200, 'capacidad': 60},
    'Standard': {'cantidad': 10, 'precio': 850, 'capacidad': 50},
    'LowCost': {'cantidad': 5, 'precio': 600, 'capacidad': 45}
}

print(f"🚀 Generando simulación {ANIO_FISCAL}...")

# --- 2. GENERACIÓN DE DATOS (Lógica pura, sin formato) ---

# A. Residencias
residencias = []
counter = 1
for tipo, data in TIPOS_RESIDENCIA.items():
    for _ in range(data['cantidad']):
        nombre = f"Residencia {tipo} {counter}"
        if tipo == 'Premium' and counter <= 5: 
            nombre = f"Residencia {['Sol','Nova','Elite','Royal','Zenith'][counter-1]}"
        residencias.append({
            'id_residencia': f'RES-{counter:02d}', 'nombre': nombre, 'tipo': tipo,
            'precio_base': float(data['precio']), 'capacidad': int(data['capacidad'])
        })
        counter += 1
df_residencias = pd.DataFrame(residencias)

# B. Estudiantes
estudiantes = []
res_list = residencias
idx = 0
for i in range(1, NUM_ESTUDIANTES + 1):
    res = res_list[idx % len(res_list)]
    idx += 1
    estudiantes.append({
        'id_estudiante': f'EST-{i:04d}', 'nombre': f'Estudiante {i}',
        'email': f'estudiante{i}@email.com', 'telefono': 600000000 + i,
        'residencia': res['nombre'], 'habitacion': random.randint(101, 599),
        'fecha_entrada': datetime(2024, 9, 1), 'cuota_mensual': float(res['precio_base'])
    })
df_estudiantes = pd.DataFrame(estudiantes)

# C. Facturas & Morosidad
morosos_ids = np.random.choice(df_estudiantes['id_estudiante'], 50, replace=False)
perfiles = {}
for i, uid in enumerate(morosos_ids):
    if i < 20: perfiles[uid] = 'Despistado'
    elif i < 40: perfiles[uid] = 'Intermitente'
    else: perfiles[uid] = 'Incobrable'

facturas = []
num_fac = 1
for mes in range(1, 13):
    f_emision = datetime(ANIO_FISCAL, mes, 1)
    f_venc = f_emision + timedelta(days=5)
    
    for _, stu in df_estudiantes.iterrows():
        uid = stu['id_estudiante']
        estado = 'pagada'
        f_pago = f_emision + timedelta(days=random.randint(0, 4))
        
        if uid in perfiles:
            p = perfiles[uid]
            if p == 'Despistado': f_pago = f_emision + timedelta(days=random.randint(15, 25))
            elif p == 'Intermitente':
                if random.random() < 0.3: 
                    f_pago = pd.NaT; estado = 'vencida' if mes < 12 else 'pendiente'
                else: f_pago = f_emision + timedelta(days=random.randint(20, 60))
            elif p == 'Incobrable':
                if mes >= 9: f_pago = pd.NaT; estado = 'impagada'
        
        facturas.append({
            'id_factura': f'FAC-{ANIO_FISCAL}-{num_fac:06d}',
            'id_estudiante': uid, 'residencia': stu['residencia'],
            'concepto': f'Alquiler {f_emision.strftime("%B %Y")}',
            'importe': stu['cuota_mensual'],
            'fecha_emision': f_emision, 'fecha_vencimiento': f_venc,
            'estado': estado, 
            'fecha_pago_real': f_pago
        })
        num_fac += 1
df_facturas = pd.DataFrame(facturas)

# D. Resto de DataFrames
df_ocup = df_residencias.copy().rename(columns={'nombre':'residencia', 'precio_base':'precio_medio'})
df_ocup['ocupacion_actual'] = df_ocup['capacidad'] - np.random.randint(0, 3, size=len(df_ocup))
df_ocup = df_ocup[['residencia','capacidad','ocupacion_actual','precio_medio']]

activos = []
for _, r in df_residencias.iterrows():
    val = r['precio_base'] * 2000
    activos.append({
        'id_activo': f"ACT-{r['id_residencia'][-2:]}", 'descripcion': f"Edificio {r['nombre']}",
        'categoria': 'Inmuebles', 'valor_adquisicion': val,
        'amortizacion_acumulada': 200000.0, 'valor_neto': val - 200000.0,
        'vida_util_anos': 50, 'fecha_adquisicion': datetime(2015, 1, 1)
    })
df_activos = pd.DataFrame(activos)

deudas = []
for _, r in df_residencias.iterrows():
    deudas.append({
        'id_prestamo': f"PREST-{r['id_residencia'][-2:]}", 'entidad': 'Banco Sim',
        'tipo': f"Hipoteca {r['nombre']}", 'capital_pendiente': 800000.0,
        'cuota_mensual': 4500.0, 'tipo_interes': 3.5,
        'fecha_vencimiento': datetime(2040, 1, 1)
    })
df_deuda = pd.DataFrame(deudas)

df_kpis = pd.DataFrame([
    {'nombre': 'Ocupación media', 'valor': 98.5, 'objetivo': 95.0, 'unidad': '%'},
    {'nombre': 'Tasa de morosidad', 'valor': 5.0, 'objetivo': 2.0, 'unidad': '%'},
    {'nombre': 'DSO', 'valor': 35.5, 'objetivo': 30.0, 'unidad': 'días'},
    {'nombre': 'EBITDA', 'valor': 3200000.0, 'objetivo': 3000000.0, 'unidad': '€'}
])

df_gastos = pd.DataFrame([{'concepto': 'Personal', 'categoria': 'RRHH', 'importe_mensual': 150000.0, 'periodicidad': 'mensual'}])
df_mant = pd.DataFrame([{'id': 'M-01', 'activo': 'Residencia Sol', 'tipo': 'Prev', 'descripcion': 'Ascensor', 'proximo_mantenimiento': datetime(2025,6,15), 'coste_estimado': 500.0, 'proveedor': 'Otis'}])
df_pagos = pd.DataFrame([{'id': 'P-01', 'proveedor': 'Iberdrola', 'concepto': 'Luz', 'importe': 4500.0, 'fecha_vencimiento': datetime(2026,1,15), 'prioridad': 'Alta'}])
df_fiscal = pd.DataFrame([{'modelo': '303', 'concepto': 'IVA 4T', 'periodo': '4T', 'fecha_limite': datetime(2026,1,30), 'estado': 'pdte', 'importe_estimado': 45000.0}])
df_caja = pd.DataFrame([{'banco': 'Santander', 'cuenta': 'ES00...', 'tipo': 'Corriente', 'saldo': 850000.0}])
df_balance = pd.DataFrame([{'cuenta': 'Activo', 'tipo': 'Act', 'importe': 35000000.0}, {'cuenta': 'Pasivo', 'tipo': 'Pas', 'importe': 20000000.0}])
df_pnl = pd.DataFrame([{'concepto': 'Ventas', 'tipo': 'Ing', 'importe': 10500000.0}])
df_iva_r = pd.DataFrame([{'concepto': 'Alquiler', 'base': 10000000.0, 'tipo': 10.0, 'cuota': 1000000.0}])
df_iva_s = pd.DataFrame([{'concepto': 'Gastos', 'base': 5000000.0, 'tipo': 21.0, 'cuota': 1050000.0}])
df_desv = pd.DataFrame([{'concepto': 'Ventas', 'presupuesto': 10000000.0, 'real': 10500000.0}])

# --- 3. EXPORTACIÓN DOBLE VÍA ---

archivos = {
    'estudiantes.csv': df_estudiantes,
    'facturas_emitidas.csv': df_facturas,
    'ocupacion.csv': df_ocup,
    'activos_fijos.csv': df_activos,
    'deuda_bancaria.csv': df_deuda,
    'gastos_fijos.csv': df_gastos,
    'kpis.csv': df_kpis,
    'mantenimientos.csv': df_mant,
    'pagos_pendientes.csv': df_pagos,
    'obligaciones_fiscales.csv': df_fiscal,
    'posicion_caja.csv': df_caja,
    'balance.csv': df_balance,
    'cuenta_resultados.csv': df_pnl,
    'iva_repercutido.csv': df_iva_r,
    'iva_soportado.csv': df_iva_s,
    'desviaciones.csv': df_desv
}

print("\n--- Guardando Archivos ---")

for nombre, df in archivos.items():
    
    # 1. VERSIÓN AGENTES (Machine Readable)
    # Formato: 2025-12-31 | 1200.50 | Separador: Coma
    path_agente = os.path.join(DIR_AGENTES, nombre)
    df.to_csv(path_agente, index=False, sep=',', decimal='.', date_format='%Y-%m-%d', encoding='utf-8')
    
    # 2. VERSIÓN EXCEL (Human Readable - Spain)
    # Formato: 31/12/2025 | 1.200,50 | Separador: Punto y coma
    path_excel = os.path.join(DIR_EXCEL, nombre)
    df.to_csv(path_excel, index=False, sep=';', decimal=',', date_format='%d/%m/%Y', encoding='utf-8-sig')
    
    print(f"✅ {nombre}: Guardado en ambas carpetas.")

print(f"\n🎉 ¡LISTO! \n👉 Usa los archivos de '{DIR_AGENTES}' para tus agentes de IA.")
print(f"👉 Usa los archivos de '{DIR_EXCEL}' para abrir en tu Excel.")