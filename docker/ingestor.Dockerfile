FROM python:3.11-slim

WORKDIR /app

# 1. Instalar dependencias y cron
RUN apt-get update && apt-get install -y \
    cron \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. CREAR EL CRON DIRECTAMENTE (Horarios de Producción CEIABD)
RUN echo "00 22 * * * python /app/src/bronze/ingest_prices.py >> /app/data/bronze/prices.log 2>&1" > /etc/cron.d/solar-cron && \
    echo "05 22 * * * python /app/src/bronze/ingest_meteo.py >> /app/data/bronze/meteo.log 2>&1" >> /etc/cron.d/solar-cron && \
    echo "55 23 * * * python /app/src/bronze/ingest_solar.py >> /app/data/bronze/solar.log 2>&1" >> /etc/cron.d/solar-cron && \
    echo "" >> /etc/cron.d/solar-cron && \
    chmod 0644 /etc/cron.d/solar-cron && \
    crontab /etc/cron.d/solar-cron

# 4. Iniciar cron
CMD ["sh", "-c", "cron && tail -f /dev/null"]
