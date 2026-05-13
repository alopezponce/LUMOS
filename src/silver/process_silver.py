import os
import sys
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_config import engine

def process_silver():
    print(f"[{datetime.now()}]  Iniciando proceso ETL de Bronze a Silver...")
    try:
        # 1. SALVAGUARDIA: Leer el histórico que ya existe en Silver para NO PERDERLO
        try:
            df_silver_historico = pd.read_sql("SELECT * FROM master_silver", engine)
            df_silver_historico['timestamp'] = pd.to_datetime(df_silver_historico['timestamp'], utc=True)
        except:
            print("No se encontró histórico en Silver. Se creará desde cero.")
            df_silver_historico = pd.DataFrame()

        # 2. Leer lo nuevo de las tablas Bronze
        df_solar = pd.read_sql("SELECT * FROM solar_bronze", engine)
        df_meteo = pd.read_sql("SELECT * FROM meteo_bronze", engine)
        try:
            df_precios = pd.read_sql("SELECT * FROM precios_bronze", engine)
        except:
            df_precios = pd.DataFrame(columns=['timestamp', 'precio_mwh'])

        # Convertir fechas a UTC estricto
        df_solar['timestamp'] = pd.to_datetime(df_solar['timestamp'], utc=True)
        df_meteo['timestamp'] = pd.to_datetime(df_meteo['timestamp'], utc=True)
        if not df_precios.empty:
            df_precios['timestamp'] = pd.to_datetime(df_precios['timestamp'], utc=True)

        # 3. Procesar y agrupar lo nuevo por horas
        df_solar_h = df_solar.set_index('timestamp').resample('h').mean().reset_index()
        df_meteo_h = df_meteo.drop_duplicates(subset=['timestamp'])
        df_precios_h = df_precios.drop_duplicates(subset=['timestamp'])

        # 4. Unir las tablas Bronze en un bloque temporal
        df_master_nuevo = pd.merge(df_solar_h, df_meteo_h, on='timestamp', how='outer')
        if not df_precios_h.empty:
            df_master_nuevo = pd.merge(df_master_nuevo, df_precios_h, on='timestamp', how='left')
        else:
            df_master_nuevo['precio_mwh'] = None

        # 5. UPSERT MLOPS: Fusionar el Histórico con lo Nuevo
        if not df_silver_historico.empty:
            # Juntamos lo viejo y lo nuevo
            df_final = pd.concat([df_silver_historico, df_master_nuevo])
            # Si hay fechas repetidas, nos quedamos con la versión más 'fresca' (last)
            df_final = df_final.drop_duplicates(subset=['timestamp'], keep='last')
        else:
            df_final = df_master_nuevo

        # 6. Limpiar, ordenar y guardar
        df_final = df_final.sort_values('timestamp').reset_index(drop=True)
        df_final.to_sql('master_silver', engine, if_exists='replace', index=False)

        print(f"¡Éxito! Master_silver actualizada de forma segura. Total de filas ahora: {len(df_final)}")

    except Exception as e:
        print(f"Error crítico en process_silver: {e}")

if __name__ == "__main__":
    process_silver()
