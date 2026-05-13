import os
import pandas as pd
from fusion_solar_py.client import FusionSolarClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()

def download_all_solar_history():
    # --- CONFIGURACIÓN ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(os.path.join(base_dir, "../../data/bronze/solar_historical.csv"))
    
    user = os.getenv("FUSION_USER")
    pswd = os.getenv("FUSION_PASS")
    station_id = os.getenv("STATION_ID", "NE=157855211")

    # Rango de fechas: Desde el 21-09-2024 hasta ayer
    start_date = datetime(2024, 9, 21)
    end_date = datetime.now() - timedelta(days=1)
    current_date = start_date

    all_dataframes = []

    print(f"🚀 Iniciando Gran Ingesta Solar desde {start_date.date()}...")

    try:
        client = FusionSolarClient(user, pswd)
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"📥 Pidiendo datos de Huawei para: {date_str}...", end="\r")
            
            # Usamos el método get_plant_stats pasando la fecha específica
            # Nota: Si tu versión de la librería no acepta fecha, me lo dices,
            # pero normalmente aceptan el parámetro 'date'
            try:
                data = client.get_plant_stats(station_id, date=current_date)
                
                if data and 'xAxis' in data:
                    prod = [float(v) if v != '--' else 0.0 for v in data['productPower']]
                    cons = [float(v) if v != '--' else 0.0 for v in data['usePower']]
                    
                    df_day = pd.DataFrame({
                        'timestamp': data['xAxis'],
                        'production_kw': prod,
                        'consumption_kw': cons
                    })
                    all_dataframes.append(df_day)
            except Exception as day_error:
                print(f"\n⚠️ Error en día {date_str}: {day_error}")
            
            # Pausa de seguridad para que Huawei no nos bloquee
            time.sleep(1.5)
            current_date += timedelta(days=1)

        # --- GUARDADO FINAL ---
        if all_dataframes:
            df_total = pd.concat(all_dataframes).drop_duplicates()
            df_total.to_csv(output_path, index=False)
            print(f"\n✅ ¡MISIÓN CUMPLIDA! {len(df_total)} registros guardados en: {output_path}")
        else:
            print("\n❌ No se recuperaron datos. Revisa la conexión.")

    except Exception as e:
        print(f"\n❌ Error crítico: {e}")

if __name__ == "__main__":
    download_all_solar_history()
