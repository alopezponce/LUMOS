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

La estructura del repositorio refleja la arquitectura de datos del sistema, manteniendo el entorno limpio para entornos de producción:

```text
LUMOS/
├── app/
│   ├── assets/
│   │   └── logo.png              # Logo del Dashboard
│   └── dashboard.py              # Interfaz web principal (Streamlit)
├── data/
│   └── bronze/                   # Almacenamiento local temporal de descargas CSV
├── docker/
│   └── ingestor.Dockerfile       # Imagen base con Python y dependencias para el ETL
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
 ```

## ⚙️ Automatización ETL (Crontab)

El pipeline de ingesta se ejecuta de forma completamente desatendida mediante trabajos Cron configurados en el host del servidor, disparando los scripts dentro del contenedor Docker:

| Hora | Proceso | Objetivo |
| :--- | :--- | :--- |
| **22:30** | `ingest_prices.py` | Obtención de tarifas eléctricas para el día siguiente (D+1). |
| **23:50** | `ingest_meteo.py` | Recogida de predicciones meteorológicas horarias. |
| **23:55** | `ingest_solar.py` | Extracción de datos del inversor de la jornada actual. |
| **00:00** | `process_silver.py`| Transformación, limpieza y subida a la capa analítica. |
| **00:05** | `notifier.py` | Envío automático del reporte de energía por Telegram. |

## 💻 Instalación y Despliegue

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/lumos.git](https://github.com/tu-usuario/lumos.git)
   cd lumos

2. **Configurar credenciales:**
   Renombra el archivo `.env.example` a `.env` e introduce tus claves de acceso a la base de datos, credenciales del inversor y el Token de tu bot de Telegram.

3. **Levantar infraestructura:**
   Ejecuta Docker Compose para construir las imágenes e iniciar tanto la base de datos como los servicios asociados.

   ```bash
   docker compose up -d --build
   ```

4. **Acceder al panel de control:**
   Abre tu navegador web e ingresa a `http://localhost:8501`.

## 👨‍💻 Autor

**Adrià** - Estudiante de la Especialización en Inteligencia Artificial y Big Data.
