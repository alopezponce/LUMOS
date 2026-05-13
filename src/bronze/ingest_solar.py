import sys
import os
import pandas as pd
from datetime import datetime
from fusion_solar_py.client import FusionSolarClient

# Añadimos la ruta para encontrar database_config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_config import engine

def ingest_solar():
    hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{hora_actual}] ☀️ Iniciando ingesta REAL de Fusion Solar...")

    # --- CONFIGURACIÓN HUAWEI ---
    user = os.getenv("FUSION_USER")
    pswd = os.getenv("FUSION_PASS")
    station_id = os.getenv("STATION_ID", "NE=157855211")

    try:
        if not user or not pswd:
            raise ValueError("Faltan credenciales FUSION_USER o FUSION_PASS en el .env")

        client = FusionSolarClient(user, pswd)
        data = client.get_plant_stats(station_id)

        if data and 'xAxis' in data:
            # 1. Limpieza de datos (Producción y Consumo)
            prod = [float(v) if v != '--' else 0.0 for v in data['productPower']]
            
            # Extraemos el consumo (Huawei suele mandarlo como 'usePower')
            # Usamos .get() por si acaso algún día Huawei no lo envía, que no crashee el script poniendo 0s
            cons = [float(v) if v != '--' else 0.0 for v in data.get('usePower', [0] * len(data['xAxis']))]

            df = pd.DataFrame({
                'timestamp': data['xAxis'],
                'production_kw': prod,
                'consumption_kw': cons # <- Añadido a la tabla
            })

            # 2. Formateo estricto de fechas (Big Data)
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')

            if len(str(df['timestamp'].iloc[0])) <= 5:
                df['timestamp'] = pd.to_datetime(fecha_hoy + ' ' + df['timestamp'].astype(str))
            else:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # 3. Guardado en PostgreSQL
            df.to_sql('solar_bronze', engine, if_exists='append', index=False)
            print(f"✅ ¡Éxito! Se han guardado {len(df)} registros reales (producción y consumo) en 'solar_bronze'.")

        else:
            print("⚠️ La API de Fusion Solar no devolvió datos válidos para hoy.")

    except Exception as e:
        print(f"❌ Error crítico en la ingesta solar: {e}")

if __name__ == "__main__":
    ingest_solar()
