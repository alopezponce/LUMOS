import os
from datetime import datetime

def rename_bronze_files():
    base_path = "/app/data/bronze"
    # Usamos la fecha de ayer porque los datos que acabas de descargar son los del día que acaba de pasar
    tag = datetime.now().strftime('%Y-%m-%d')
    
    # Mapeo de archivos: Nombre original -> Nombre con fecha
    files_to_rename = {
        "meteo_raw.csv": f"meteo_{tag}.csv",
        "solar_raw.csv": f"solar_{tag}.csv"
    }

    print(f"Organizando archivos del día {tag}...")

    for original, new_name in files_to_rename.items():
        old_path = os.path.join(base_path, original)
        new_path = os.path.join(base_path, new_name)

        if os.path.exists(old_path):
            # Cambiamos el nombre (rename)
            os.rename(old_path, new_path)
            print(f"{original} -> {new_name}")
        else:
            print(f"o se encontró {original}, saltando...")

if __name__ == "__main__":
    rename_bronze_files()
