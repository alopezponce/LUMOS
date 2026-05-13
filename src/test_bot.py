import telebot
import os
import pandas as pd
import sys
from datetime import datetime

# Añadimos la ruta para encontrar database_config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_config import engine

# Configuración (Asegúrate de que estas variables están en tu .env)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TOKEN)

def prueba_bot_db():
    print(f"[{datetime.now()}] 🤖 Iniciando prueba de Bot + DB...")
    
    try:
        # 1. Intentamos leer algo de la base de datos
        query = "SELECT precio_mwh FROM precios_bronze ORDER BY timestamp DESC LIMIT 1"
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            ultimo_precio = df['precio_mwh'].iloc[0]
            mensaje = (
                f"🚀 *¡Prueba Exitosa!*\n\n"
                f"📡 *Estado:* Conectado a Docker DB\n"
                f"💰 *Último precio leído:* {ultimo_precio} €/MWh\n"
                f"📅 *Hora:* {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            mensaje = "⚠️ Conectado a la DB, pero la tabla de precios parece vacía."

        # 2. Enviar el mensaje a Telegram
        bot.send_message(CHAT_ID, mensaje, parse_mode='Markdown')
        print("✅ Mensaje enviado a Telegram correctamente.")

    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    prueba_bot_db()
