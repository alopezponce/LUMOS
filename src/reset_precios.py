import requests
import pandas as pd
import sys
import os
import time
from datetime import datetime
from sqlalchemy import text

# Encontrar database_config.py
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def reset_y_rellenar_precios():
    print(f"[{datetime.now()}] 🚀 Iniciando DESCARGA MASIVA de precios PVPC (Nov 2024 - Hoy)...")
    
    # 1. Limpiar la tabla Bronze de precios
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS precios_bronze CASCADE;"))
        print("🧹 Tabla 'precios_bronze' reseteada. Empezamos de cero.")
    except Exception as e:
        print(f"Aviso al limpiar: {e}")

    # 2. Bucle para descargar MES a MES y no saturar la API
    start_date = '2024-11-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    meses = pd.date_range(start=start_date, end=end_date, freq='MS')
    all_prices = []

    for start_mes in meses:
        # Calculamos el final del mes
        end_mes = start_mes + pd.offsets.MonthEnd(0)
        # Si el fin de mes supera el día de hoy, cortamos hoy
        if end_mes > pd.to_datetime(end_date):
            end_mes = pd.to_datetime(end_date)
            
        str_start = start_mes.strftime('%Y-%m-%d')
        str_end = end_mes.strftime('%Y-%m-%d')
        
        print(f"⏳ Descargando precios del mes: {str_start} al {str_end}...")
        
        url = f"https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?start_date={str_start}T00:00&end_date={str_end}T23:59&time_trunc=hour"
        
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                pvpc_data = None
                for item in data.get('included', []):
                    if item.get('id') == '1001':
                        pvpc_data = item['attributes']['values']
                        break
                        
                if pvpc_data:
                    df_month = pd.DataFrame(pvpc_data)
                    df_month = df_month[['datetime', 'value']]
                    df_month.columns = ['timestamp', 'precio_mwh']
                    all_prices.append(df_month)
                    print(f"   ✅ Extraídas {len(df_month)} horas.")
            else:
                print(f"   ⚠️ Fallo en el mes {str_start}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error en {str_start}: {e}")
            
        # Pausa de 1 segundo para que REE no nos detecte como atacantes
        time.sleep(1) 
        
    if all_prices:
        # 3. Guardar el histórico gigantesco en Bronze
        print("\n💾 Guardando el histórico completo en 'precios_bronze'...")
        df_final = pd.concat(all_prices, ignore_index=True)
        df_final['timestamp'] = pd.to_datetime(df_final['timestamp'], utc=True)
        df_final = df_final.drop_duplicates(subset=['timestamp'])
        df_final.to_sql('precios_bronze', engine, if_exists='replace', index=False)
        
        # 4. Inyectar en la tabla maestra Silver
        print("🧬 Amputando columna vieja e inyectando los precios perfectos en 'master_silver'...")
        df_master = pd.read_sql("SELECT * FROM master_silver", engine)
        df_master['timestamp'] = pd.to_datetime(df_master['timestamp'], utc=True)
        
        # Borramos la columna rota
        if 'precio_mwh' in df_master.columns:
            df_master = df_master.drop(columns=['precio_mwh'])
            
        # Pegamos el precio nuevo al lado del clima y la producción que ya tienes
        df_master_actualizado = pd.merge(df_master, df_final, on='timestamp', how='left')
        
        # Sobrescribimos
        df_master_actualizado.to_sql('master_silver', engine, if_exists='replace', index=False)
        print(f"🎉 ¡ÉXITO ROTUNDO! Se han rellenado los precios en la base de datos definitiva.")
    else:
        print("❌ No se pudo descargar ningún precio.")

if __name__ == "__main__":
    reset_y_rellenar_precios()
