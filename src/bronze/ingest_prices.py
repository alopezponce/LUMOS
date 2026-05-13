import requests
import pandas as pd
import sys
import os
from datetime import datetime

# Añadimos la ruta para encontrar database_config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_config import engine

def ingest_prices():
    print(f"[{datetime.now()}] 💰 Iniciando ingesta de precios PVPC (REE Open Data)...")

    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    
    # URL de la API de Datos Abiertos de REE (¡No necesita Token!)
    url = f"https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?start_date={fecha_hoy}T00:00&end_date={fecha_hoy}T23:59&time_trunc=hour"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Buscamos específicamente el indicador 1001 (PVPC) dentro de la respuesta
        pvpc_data = None
        for item in data.get('included', []):
            if item.get('id') == '1001':
                pvpc_data = item['attributes']['values']
                break
        
        if pvpc_data:
            df = pd.DataFrame(pvpc_data)
            
            # Seleccionamos y renombramos columnas
            df = df[['datetime', 'value']]
            df.columns = ['timestamp', 'precio_mwh']

            # Convertimos el timestamp a formato fecha de Python UTC
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # GUARDADO EN POSTGRESQL
            df.to_sql('precios_bronze', engine, if_exists='append', index=False)

            print(f"✅ ¡Éxito! Se han guardado {len(df)} precios en 'precios_bronze'.")
        else:
            print("⚠️ La API de REE no devolvió valores de PVPC para hoy.")

    except Exception as e:
        print(f"❌ Error en la ingesta de precios: {e}")

if __name__ == "__main__":
    ingest_prices()
