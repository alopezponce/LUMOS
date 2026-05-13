import pandas as pd
import sys
import os
from datetime import datetime

# Conectar con la base de datos
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def cargar_historico_silver():
    # La ruta donde Docker ve la carpeta data
    ruta_csv = '/app/data/IA_SOLAR_CALELLA_SILVER.csv'
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando carga masiva SILVER...")
    
    if not os.path.exists(ruta_csv):
        print(f"❌ ERROR: Docker no encuentra el archivo en {ruta_csv}.")
        print("Asegúrate de haberlo subido a ~/proyectov2/data/")
        return

    try:
        # 1. Leer el CSV gigante
        print(f"⏳ Leyendo las 11.669 líneas del CSV...")
        df = pd.read_csv(ruta_csv)
        
        # 2. Asegurarnos de que el timestamp es formato fecha oficial
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        # 3. Volcar todo a PostgreSQL
        print("⏳ Escribiendo en la base de datos (esto puede tardar unos segundos)...")
        # Usamos 'replace' para que cree la tabla limpia desde cero con este CSV
        df.to_sql('master_silver', engine, if_exists='replace', index=False)
        
        print(f"✅ ¡ÉXITO TOTAL! Se han guardado {len(df)} filas en la tabla 'master_silver'.")
        
    except Exception as e:
        print(f"❌ Error durante la inyección: {e}")

if __name__ == "__main__":
    cargar_historico_silver()
