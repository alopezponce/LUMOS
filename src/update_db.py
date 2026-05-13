import os
import sys
from sqlalchemy import text

# Aseguramos que encuentre database_config
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def update_schema():
    print("🛠️ Modificando el esquema de la base de datos...")
    try:
        with engine.begin() as conn:
            # Añadimos las columnas del clima
            conn.execute(text("""
                ALTER TABLE meteo_bronze 
                ADD COLUMN IF NOT EXISTS hum FLOAT, 
                ADD COLUMN IF NOT EXISTS precip FLOAT, 
                ADD COLUMN IF NOT EXISTS rad_diffuse FLOAT, 
                ADD COLUMN IF NOT EXISTS pressure FLOAT;
            """))
            
            # Añadimos la columna de consumo solar
            conn.execute(text("""
                ALTER TABLE solar_bronze 
                ADD COLUMN IF NOT EXISTS consumption_kw FLOAT;
            """))
            
        print("✅ ¡Base de datos actualizada con éxito! Ya hay hueco para las nuevas columnas.")
    except Exception as e:
        print(f"❌ Error al actualizar: {e}")

if __name__ == "__main__":
    update_schema()
