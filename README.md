# Price Tracker Bot

Un sistema automatizado de seguimiento de precios que monitorea productos en Amazon (vía Keepa), Promodescuentos y Office Depot, enviando alertas en tiempo real a Telegram cuando se detectan bajas de precio significativas o promociones destacadas.

## Características

- Monitoreo de Múltiples Fuentes:
    - Amazon: Utiliza la API de Keepa para rastrear el historial de precios y caídas.
    - Promodescuentos: Analiza las ofertas más destacadas y nuevas publicaciones.
    - Office Depot: Monitorea páginas de productos específicos para detectar cambios de precio.
- Notificaciones por Telegram: Alertas inmediatas con detalles del producto, historial de precios y enlaces directos.
- Escaneo Automatizado: Tareas programadas utilizando Celery y Celery Beat.
- Persistencia de Datos: Almacena el historial de precios y las ofertas detectadas en PostgreSQL.
- Contenedores con Docker: Fácil despliegue utilizando Docker y Docker Compose.

## Tecnologías Utilizadas

- Lenguaje: Python 3.11+
- Cola de Tareas: Celery con Redis
- Base de Datos: PostgreSQL (SQLAlchemy ORM)
- Extracción de Datos (Scraping): BeautifulSoup4, HTTPX
- APIs: Keepa API, Telegram Bot API
- Infraestructura: Docker & Docker Compose

## Requisitos Previos

- Docker y Docker Compose instalados.
- Un token de Bot de Telegram (obtenido de @BotFather).
- Una clave de API de Keepa (obtenida de Keepa.com).

## Configuración e Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/luis-guizar/price_scrapper.git
   cd price_scrapper
   ```

2. Configurar Variables de Entorno:
   Copia el archivo de ejemplo y completa tus credenciales:
   ```bash
   cp .env.example .env
   ```
   Edita el archivo .env con tus valores para KEEPA_API_KEY, TELEGRAM_TOKEN y TELEGRAM_CHAT_ID.

3. Desplegar con Docker:
   ```bash
   docker-compose up --build -d
   ```

## Estructura del Proyecto

- app/: Código principal de la aplicación.
    - tasks.py: Definición de las tareas de Celery para el escaneo.
    - keepa_service.py: Lógica de integración con Amazon/Keepa.
    - promodescuentos_service.py: Extracción de datos de Promodescuentos.
    - officedepot_service.py: Extracción de datos de Office Depot.
    - models.py: Modelos de base de datos SQLAlchemy.
    - celery_app.py: Configuración de Celery y cronograma de tareas.
- docker-compose.yaml: Orquestación para el Worker, Beat, Redis y Postgres.
- Dockerfile: Configuración de la imagen para producción.

## Desarrollo

### Configuración Local (sin Docker)

1. Crear un entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Asegúrate de tener Redis y Postgres funcionando localmente e inicia el worker:
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

4. Inicia el programador (Beat):
   ```bash
   celery -A app.celery_app beat --loglevel=info
   ```

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, siéntete libre de enviar un Pull Request.
