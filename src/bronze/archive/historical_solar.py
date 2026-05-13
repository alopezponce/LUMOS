import pandas as pd
import os
import glob

def process_historical_solar():
    # Rutas dentro del contenedor
    path_bronze = "/app/data/bronze"
    output_path = f"{path_bronze}/solar_historical.csv"

    print("☀️ Iniciando consolidación del histórico solar...")

    # Buscamos si hay un archivo 'gordo' de exportación manual o archivos sueltos antiguos
    # Si en el instituto te dan un archivo llamado 'export_huawei.csv', ponlo en data/bronze
    manual_export = os.path.join(path_bronze, "export_huawei.csv")
    
    if os.path.exists(manual_export):
        print(f"📄 Detectado archivo de exportación manual: {manual_export}")
        df = pd.read_csv(manual_export)
        
        # --- LÓGICA DE LIMPIEZA ESTÁNDAR PARA HUAWEI ---
        # 1. Intentar detectar la columna de tiempo (suele ser la primera)
        df['timestamp'] = pd.to_datetime(df.iloc[:, 0])
        
        # 2. Intentar detectar la columna de potencia (Active Power / Producción)
        # Aquí renombramos la columna que contenga 'Power' o 'kW' a 'production_kw'
        for col in df.columns:
            if 'Power' in col or 'kw' in col.lower():
                df = df.rename(columns={col: 'production_kw'})
                break
        
        df = df[['timestamp', 'production_kw']]
        print(f"✅ Procesado archivo manual con {len(df)} registros.")

    else:
        print("🔍 No hay archivo manual. Buscando archivos diarios 'solar_202*.csv' para unificar...")
        solar_files = glob.glob(f"{path_bronze}/solar_202*.csv")
        
        if not solar_files:
            print("⚠️ No se han encontrado archivos solares antiguos para procesar.")
            return

        # Unimos todos los diarios que ya tengas en el servidor
        df_list = []
        for f in solar_files:
            temp_df = pd.read_csv(f)
            # Aseguramos que tengan la columna timestamp
            if 'timestamp' in temp_df.columns:
                df_list.append(temp_df)
        
        df = pd.concat(df_list).drop_duplicates()
        print(f"✅ Unificados {len(solar_files)} archivos diarios.")

    # Guardar el resultado final
    df.to_csv(output_path, index=False)
    print(f"💾 Guardado histórico solar en: {output_path}")
    print("-" * 30)

if __name__ == "__main__":
    process_historical_solar()
