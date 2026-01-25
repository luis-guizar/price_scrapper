import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_telegram_message(message):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token:
        print("❌ Error: TELEGRAM_TOKEN not found in environment.")
        return False
    if not chat_id:
        print("❌ Error: TELEGRAM_CHAT_ID not found in environment.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # We'll support some basic HTML formatting if the user includes it, 
    # but the primary goal is just sending the update.
    # Adding an emoji to make it look official like the bot updates
    formatted_message = f"📢 ACTUALIZACIÓN\n\n{message}"

    payload = {
        "chat_id": chat_id,
        "text": formatted_message,
        # "parse_mode": "Markdown" # Removed to avoid errors with special characters in user message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent successfully!")
            return True
        else:
            print(f"❌ Failed to send message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send an update to the Telegram group chat via the bot.")
    parser.add_argument("message", help="The message text to send.")
    
    # If no arguments are passed, print help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    
    send_telegram_message(args.message)
