import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_test_alert():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("❌ Variables de entorno TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no configuradas")
        return

    msg = "🚀 Esto es una prueba de alerta de Telegram desde el Price Tracker. PD: La Josa MLP MLP MLP MLP"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Alerta de prueba enviada correctamente a Telegram.")
        else:
            print(f"❌ Error enviando alerta Telegram: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Excepción enviando alerta: {e}")

if __name__ == "__main__":
    send_test_alert()
