# Price Tracker Bot 📈

A powerful, automated price tracking system that monitors products on Amazon (via Keepa), Promodescuentos, and Office Depot, sending real-time alerts to Telegram when significant price drops or deals are detected.

## 🚀 Features

- **Multi-Source Tracking**: 
  - **Amazon**: Uses Keepa API to track price history and drops.
  - **Promodescuentos**: Scrapes hot deals and new postings.
  - **Office Depot**: Monitors specific product pages for price changes.
- **Telegram Notifications**: Immediate alerts with product details, price history, and direct links.
- **Automated Scanning**: Scheduled tasks using Celery and Celery Beat.
- **Data Persistence**: Stores price history and detected deals in PostgreSQL.
- **Dockerized**: Easy deployment using Docker and Docker Compose.

## 🛠 Tech Stack

- **Language**: Python 3.11+
- **Task Queue**: Celery with Redis
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Scraping**: BeautifulSoup4, HTTPX
- **APIs**: Keepa API, Telegram Bot API
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed.
- A Telegram Bot token (from [@BotFather](https://t.me/botfather)).
- A Keepa API Key (from [Keepa.com](https://keepa.com/#!api)).

## ⚙️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/price-tracker.git
   cd price-tracker
   ```

2. **Configure Environment Variables**:
   Copy the example environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your `KEEPA_API_KEY`, `TELEGRAM_TOKEN`, and `TELEGRAM_CHAT_ID`.

3. **Deploy with Docker**:
   ```bash
   docker-compose up --build -d
   ```

## 📂 Project Structure

- `app/`: Main application code.
  - `tasks.py`: Celery task definitions for scanning.
  - `keepa_service.py`: Amazon/Keepa integration logic.
  - `promodescuentos_service.py`: Web scraping for Promodescuentos.
  - `officedepot_service.py`: Web scraping for Office Depot.
  - `models.py`: SQLAlchemy database models.
  - `celery_app.py`: Celery configuration and schedule.
- `docker-compose.yaml`: Orchestration for Worker, Beat, Redis, and Postgres.
- `Dockerfile`: Production-ready image configuration.

## 🛠 Development

### Local Setup (without Docker)

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have Redis and Postgres running locally, then start the worker:
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

4. Start the scheduler (Beat):
   ```bash
   celery -A app.celery_app beat --loglevel=info
   ```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
