import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def reset_database():
    print("💥 Iniciando protocolo de reseteo...")
    try:
        with engine.begin() as conn:
            # CASCADE fuerza el borrado aunque haya dependencias
            conn.execute(text("DROP TABLE IF EXISTS master_silver CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS meteo_bronze CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS solar_bronze CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS precios_bronze CASCADE;"))
            
        print("✅ Tablas eliminadas. Base de datos limpia y lista para reconstruir.")
    except Exception as e:
        print(f"❌ Error al resetear: {e}")

if __name__ == "__main__":
    reset_database()
