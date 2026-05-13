import os
import sys
import pandas as pd
from datetime import datetime

# Encontrar database_config.py
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def restaurar_desde_csv():
    print(f"[{datetime.now()}] 🚑 Iniciando restauración desde archivo CSV...")
    
    # Ruta exacta del archivo que me has pasado
    csv_path = os.path.join(os.path.dirname(__file__), 'IA_SOLAR_CALELLA_SILVER_2.csv')
    
    try:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"No encuentro el archivo {csv_path}. Asegúrate de que está en la misma carpeta que este script.")

        # 1. Leer el CSV de rescate
        print("📄 Leyendo CSV...")
        df_csv = pd.read_csv(csv_path)
        df_csv['timestamp'] = pd.to_datetime(df_csv['timestamp'], utc=True)
        
        # 2. Leer lo que ha sobrevivido en la base de datos (los últimos 4 días)
        print("🗄️ Leyendo base de datos actual...")
        try:
            df_actual = pd.read_sql("SELECT * FROM master_silver", engine)
            df_actual['timestamp'] = pd.to_datetime(df_actual['timestamp'], utc=True)
        except Exception as e:
            print(f"Aviso (Tabla vacía o inexistente): {e}")
            df_actual = pd.DataFrame()

        # 3. FUSIÓN MÁGICA (Upsert)
        print("🧬 Fusionando el pasado y el presente...")
        df_final = pd.concat([df_actual, df_csv])
        
        # Eliminamos duplicados dando prioridad a los datos más recientes
        df_final = df_final.drop_duplicates(subset=['timestamp'], keep='first')
        
        # Ordenamos cronológicamente
        df_final = df_final.sort_values('timestamp').reset_index(drop=True)

        # 4. Guardamos la tabla Maestra restaurada
        print("💾 Guardando en PostgreSQL...")
        df_final.to_sql('master_silver', engine, if_exists='replace', index=False)
        
        print(f"✅ ¡RESTAURACIÓN COMPLETADA! Tu tabla 'master_silver' ha resucitado con {len(df_final)} filas.")

    except Exception as e:
        print(f"❌ Error crítico en la restauración: {e}")

if __name__ == "__main__":
    restaurar_desde_csv()
