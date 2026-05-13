import os
import sys
import pandas as pd
from datetime import datetime

# Encontrar database_config.py
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def importar_excel():
    print(f"[{datetime.now()}] 📥 Importando Producción y Consumo de Abril desde Excel...")
    
    # Nombre exacto de tu archivo
    excel_file = 'Informe de plantas_R26780 Calella_01-04-2026_30-04-2026_h.xlsx'
    excel_path = os.path.join(os.path.dirname(__file__), excel_file)
    
    try:
        # 1. Leer el Excel (empezando en la fila 1 para saltar el título de Huawei)
        print("📄 Leyendo archivo...")
        df = pd.read_excel(excel_path, sheet_name='Sheet1', header=1)
        
        # 2. Limpiar y formatear
        print("🧹 Limpiando datos (quitando etiquetas DST y formateando)...")
        df_clean = pd.DataFrame()
        
        # Quitamos el texto " DST" que ensucia las fechas
        df_clean['timestamp'] = df['Período estadístico'].str.replace(' DST', '', regex=False)
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], utc=True)
        
        # Extraemos Producción (Rendimiento FV) y Consumo
        df_clean['production_kw'] = pd.to_numeric(df['Rendimiento FV (kWh)'], errors='coerce').fillna(0)
        df_clean['consumption_kw'] = pd.to_numeric(df['Consumo (kWh)'], errors='coerce').fillna(0)
        
        # 3. Inyectar en la base de datos (solar_bronze)
        print("💾 Inyectando en la base de datos...")
        df_clean.to_sql('solar_bronze', engine, if_exists='append', index=False)
        
        print(f"✅ ¡Éxito! Se han parcheado {len(df_clean)} horas de producción y consumo en 'solar_bronze'.")
        
    except FileNotFoundError:
        print(f"❌ ¡Error! No encuentro el archivo '{excel_file}'. Asegúrate de que está en la carpeta 'src'.")
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    importar_excel()
