# ☀️ IA_SOL: Centro de Control Energético (Solar MLOps)

Este repositorio contiene el código fuente del proyecto "IA_SOL", desarrollado como trabajo final para el curso de especialización en Inteligencia Artificial y Big Data. 

El objetivo principal es predecir la producción de energía de una instalación de paneles solares mediante algoritmos de **Deep Learning (LSTM)**, y cruzar esa información con el clima y los precios del mercado eléctrico (PVPC) para optimizar el consumo de los electrodomésticos del hogar mediante un **Algoritmo Voraz**.

## 🚀 Características Principales

* **Pipeline de Ingesta Automática (ETL):** Descarga de datos programada mediante Cronjobs desde 3 APIs distintas: inversor Huawei (Fusion Solar), Open-Meteo y ESIOS (Red Eléctrica de España).
* **Arquitectura Medallón:** Los datos fluyen estructurados a través de capas lógicas (Bronze, Silver, Gold) dentro de una base de datos relacional robusta.
* **Modelo Predictivo LSTM:** Red neuronal recurrente entrenada para entender patrones temporales e inercias climáticas, alcanzando una alta precisión en la predicción a 24 horas.
* **MLOps y Monitorización:** Sistema de reentrenamiento bajo demanda (Retraining) y auditoría diaria automatizada con envío de reportes mediante un Bot de Telegram.
* **Dashboard Interactivo:** Interfaz web intuitiva para visualizar el histórico, las predicciones y la "Agenda Óptima" de consumo.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10
* **Infraestructura:** Docker & Docker Compose
* **Base de Datos:** PostgreSQL
* **Machine Learning:** TensorFlow / Keras, Scikit-Learn
* **Tratamiento de Datos:** Pandas, Numpy
* **Frontend:** Streamlit, Plotly
* **Automatización:** Linux Cron, pyTelegramBotAPI

## ⚙️ Arquitectura del Sistema

El proyecto está completamente dockerizado para garantizar su reproducibilidad. Se divide en dos contenedores principales:
1.  `db`: Servidor PostgreSQL que almacena las capas Bronze y Silver.
2.  `app`: Contenedor principal que ejecuta los scripts de ingesta, el preprocesamiento, el entrenamiento del modelo y levanta la interfaz web de Streamlit.

## 📥 Instalación y Despliegue Local

1. Clona este repositorio en tu máquina:
   ```bash
   git clone [https://github.com/alopezponce/IA_SOL.git](https://github.com/alopezponce/IA_SOL.git)
   cd IA_SOL
