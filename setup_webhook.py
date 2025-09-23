import requests
import os
from dotenv import load_dotenv

def setup_webhook():
    # Load environment variables
    load_dotenv()
    
    # Get the bot token from environment variables
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    print(f"Token found: {'Yes' if TELEGRAM_TOKEN else 'No'}")
    
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please make sure you have set TELEGRAM_BOT_TOKEN in your Railway environment variables")
        return
    
    # Get webhook URL from environment or construct from Railway URL
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    if not WEBHOOK_URL:
        # Try to construct from Railway URL
        railway_url = os.getenv("RAILWAY_STATIC_URL")
        if railway_url:
            WEBHOOK_URL = f"{railway_url}/telegram/telegram-webhook"
        else:
            print("❌ Error: WEBHOOK_URL not found in environment variables")
            print("Please set WEBHOOK_URL in your Railway environment variables")
            return
    
    # Telegram API endpoint to set webhook
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    
    print(f"Setting webhook to: {WEBHOOK_URL}")
    print(f"Using API URL: {api_url}")
    
    # Set up the webhook
    try:
        response = requests.post(
            api_url,
            json={'url': WEBHOOK_URL}
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200 and response.json().get('ok'):
            print("✅ Webhook set up successfully!")
            print(f"Webhook URL: {WEBHOOK_URL}")
        else:
            print("❌ Failed to set up webhook")
            print(f"Response: {response.json()}")
            
        # Let's also test the getWebhookInfo endpoint
        info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        info_response = requests.get(info_url)
        print("\nCurrent Webhook Info:")
        print(info_response.json())
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    setup_webhook() 