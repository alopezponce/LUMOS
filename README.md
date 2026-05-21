# ☀️ LUMOS - Plataforma Predictiva de Autoconsumo Solar con IA

![Estado](https://img.shields.io/badge/Estado-En_Producción-success)
![Versión](https://img.shields.io/badge/Versión-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

**LUMOS** es un proyecto *End-to-End* de Inteligencia Artificial y Big Data diseñado para monitorizar, predecir y optimizar el consumo energético doméstico. Utilizando datos reales de un inversor solar Huawei SUN2000, predicciones meteorológicas y los precios de la red eléctrica, el sistema recomienda cuándo encender los electrodomésticos para maximizar el ahorro.

## 🚀 Características Principales

* **Pipeline de Datos Automatizado (ETL):** Ingesta orquestada mediante Cron de datos de producción solar, clima (Open-Meteo) y precios de la electricidad.
* **Arquitectura Medallón:** Procesamiento estructurado en bases de datos PostgreSQL (Bronze para datos crudos, Silver para datos limpios, Gold para entrenamiento).
* **Inteligencia Artificial (LSTM):** Red Neuronal Recurrente (LSTM) entrenada con *Feature Engineering* para capturar la inercia del sol, superando el **0.93 de R²** en validación (80/20 split).
* **MLOps Integrado:** Re-entrenamiento del modelo y actualización dinámica del escalador (`StandardScaler`) en un solo clic desde el entorno de producción.
* **Dashboard Interactivo:** Interfaz en Streamlit con un **Planificador Inteligente de Cargas** que cruza el consumo base con la curva de producción inferida para las próximas 24 horas.
* **Sistema de Alertas:** Integración con un Bot de Telegram para el envío diario del pronóstico y resumen de ahorro.

## 📂 Estructura del Proyecto

La estructura del repositorio refleja la arquitectura de datos del sistema, excluyendo logs y archivos temporales de desarrollo:

```text
LUMOS/
├── app/
│   ├── assets/
│   │   └── logo.png              # Logo del Dashboard
│   └── dashboard.py              # Interfaz web principal (Streamlit)
├── data/
│   └── bronze/                   # Almacenamiento local temporal de descargas CSV
├── docker/
│   └── ingestor.Dockerfile       # Imagen para contenedores de ingesta ETL
├── models/
│   ├── accuracy.txt              # Registro de la métrica R² actual
│   ├── scaler.pkl                # Escalador de variables (Imprescindible para inferencia)
│   └── solar_lstm.keras          # Modelo de Red Neuronal en producción
├── src/
│   ├── bronze/                   # Capa 1: Extracción de orígenes
│   │   ├── ingest_meteo.py       # Conexión API Open-Meteo
│   │   ├── ingest_prices.py      # Conexión API Mercado Eléctrico
│   │   └── ingest_solar.py       # Conexión y parseo inversor Huawei
│   ├── silver/                   # Capa 2: Transformación
│   │   └── process_silver.py     # Limpieza, unificación y Feature Engineering
│   ├── gold/                     # Capa 3: Machine Learning
│   │   └── train_model.py        # Algoritmo de entrenamiento y MLOps
│   ├── utils/
│   │   └── notifier.py           # Gestión del Bot de Telegram
│   └── database_config.py        # Enlace SQLAlchemy con PostgreSQL
├── docker-compose.yml            # Orquestación de los servicios
├── requirements.txt              # Dependencias de Python
└── .env.example                  # Plantilla de credenciales y tokens
