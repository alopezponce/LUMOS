import os
from sqlalchemy import create_engine

# Docker inyecta estas variables desde el .env que configuramos antes
DB_USER = os.getenv("POSTGRES_USER", "iabd_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "iabd_password")
DB_NAME = os.getenv("POSTGRES_DB", "energia_db")
DB_HOST = "ia_sol_db"  # Nombre del servicio en tu docker-compose

# Creamos el motor de conexión para SQLAlchemy
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')
