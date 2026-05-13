import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

def get_meteo_historical():
    # Configuracion de cache y reintentos
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # URL de la API de archivo historico
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    # Parametros de la peticion (Calella)
    params = {
        "latitude": 41.616449,
        "longitude": 2.665698,
        "start_date": "2024-09-21",
        "end_date": "2026-04-22",
        "hourly": [
            "temperature_2m", 
            "relative_humidity_2m", 
            "precipitation", 
            "cloud_cover", 
            "shortwave_radiation", 
            "direct_radiation",
            "diffuse_radiation",
            "surface_pressure"
        ],
        "timezone": "Europe/Madrid"
    }

    print("🛰️ Pidiendo datos a la API de Open-Meteo...")
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Procesamiento de datos horarios
    hourly = response.Hourly()
    
    # Parche para evitar el error de bytes en la zona horaria
    tz_raw = response.Timezone()
    timezone_str = tz_raw.decode() if isinstance(tz_raw, bytes) else tz_raw

    # Creacion del rango de fechas
    timestamps = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(timezone_str),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(timezone_str),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )

    hourly_data = {"timestamp": timestamps}

    # Mapeo de variables segun el orden en params['hourly']
    hourly_data["temp"] = hourly.Variables(0).ValuesAsNumpy()
    hourly_data["hum"] = hourly.Variables(1).ValuesAsNumpy()
    hourly_data["precip"] = hourly.Variables(2).ValuesAsNumpy()
    hourly_data["cloud_cover"] = hourly.Variables(3).ValuesAsNumpy()
    hourly_data["rad_shortwave"] = hourly.Variables(4).ValuesAsNumpy()
    hourly_data["rad_direct"] = hourly.Variables(5).ValuesAsNumpy()
    hourly_data["rad_diffuse"] = hourly.Variables(6).ValuesAsNumpy()
    hourly_data["pressure"] = hourly.Variables(7).ValuesAsNumpy()

    # Creacion del DataFrame
    df = pd.DataFrame(data=hourly_data)
    
    # Guardado en la ruta compartida con el volumen de Docker
    output_path = "/app/data/bronze/meteo_historical.csv"
    df.to_csv(output_path, index=False)
    
    print("-" * 30)
    print(f"✅ ¡EXITO! Dataset meteo guardado.")
    print(f"📊 Total: {len(df)} filas.")
    print(f"📍 Ruta: {output_path}")
    print("-" * 30)

if __name__ == "__main__":
    get_meteo_historical()
