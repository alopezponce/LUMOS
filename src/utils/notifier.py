import telebot
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Configuración de base de datos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_config import engine

TOKEN = os.getenv("TELEGRAM_TOKEN").strip() if os.getenv("TELEGRAM_TOKEN") else None
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID").strip() if os.getenv("TELEGRAM_CHAT_ID") else None
bot = telebot.TeleBot(TOKEN)

def comprobar_estado_bronce(tabla):
    try:
        # Fijo: Siempre audita el día anterior (porque se ejecuta a las 00:05)
        fecha_objetivo = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        query = f"""SELECT count(*) FROM {tabla} WHERE "timestamp"::date = '{fecha_objetivo}'"""
        df = pd.read_sql(query, engine)
        
        if df.iloc[0, 0] > 0:
            return " Datos guardados"
        return "No encontrado"
    except Exception:
        return " Error SQL"

def obtener_conteo_silver():
    try:
        query = "SELECT count(*) FROM master_silver"
        return pd.read_sql(query, engine).iloc[0, 0]
    except Exception:
        return "N/A"

def enviar_reporte():
    ahora = datetime.now()
    fecha_emision = ahora.strftime('%d/%m/%Y %H:%M')
    fecha_auditoria = (ahora - timedelta(days=1)).strftime('%d/%m/%Y')

    st_meteo = comprobar_estado_bronce("meteo_bronze")
    st_solar = comprobar_estado_bronce("solar_bronze")
    st_precios = comprobar_estado_bronce("precios_bronze")
    total_silver = obtener_conteo_silver()

    # Formato exacto que has pedido
    mensaje = (
        f"📊 *REPORTE CEIABD-03*\n"
        f"Emisión: {fecha_emision} (Madrid)\n"
        f"Auditando datos del: *{fecha_auditoria}*\n\n"
        f"☁️ *Meteo:* {st_meteo}\n"
        f"☀️ *Solar:* {st_solar}\n"
        f"💰 *Precios (D+1):* {st_precios}\n\n"
        f"📚 *Dataset Maestro (Silver):*\n"
        f"• Total filas para IA: *{total_silver}*\n\n"
        f"✅ *Estado:* Sistema operativo."
    )

    try:
        bot.send_message(CHAT_ID, mensaje, parse_mode='Markdown')
        print("Reporte final enviado correctamente.")
    except Exception as e:
        print(f" Error al enviar mensaje: {e}")

if __name__ == "__main__":
    enviar_reporte()
