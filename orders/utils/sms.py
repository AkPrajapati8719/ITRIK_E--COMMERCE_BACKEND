import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def normalize_mobile(mobile):
    """
    Ensures Indian mobile format for gateways
    """
    mobile = str(mobile).strip()

    if mobile.startswith("+91"):
        mobile = mobile.replace("+91", "")
    elif mobile.startswith("91") and len(mobile) == 12:
        mobile = mobile[2:]

    if len(mobile) != 10:
        raise ValueError(f"Invalid mobile number format: {mobile}")

    return mobile


def send_sms(mobile, message):
    """
    Production-safe SMS sender for Fast2SMS
    """
    try:
        mobile = normalize_mobile(mobile)

        if not getattr(settings, "FAST2SMS_ENABLED", False):
            print("\n" + "="*50)
            print(f"📱 [SMS MOCK] To: {mobile}")
            print(f"✉️  Message: {message}")
            print("="*50 + "\n")
            return True

        api_key = getattr(settings, "FAST2SMS_API_KEY", None)
        if not api_key:
            print("🚨 FAST2SMS_API_KEY is missing in settings.py!")
            return False

        url = "https://www.fast2sms.com/dev/bulkV2"

        payload = {
            "route": "q",  
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": mobile,
        }

        headers = {
            "authorization": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Send request
        response = requests.post(url, data=payload, headers=headers, timeout=10)

        # Read the JSON response
        data = response.json()

        # Gateway success validation
        if data.get("return") is False:
            error_msg = data.get("message", "Unknown Fast2SMS Error")
            print(f"⚠️ Fast2SMS Error: {error_msg}")
            return False

        # 🔥 UPDATED: Print the RAW data so we can see exactly what Fast2SMS is doing!
        print(f"✅ Fast2SMS Raw Response: {data}")
        return True

    except Exception as e:
        print(f"🚨 Python Request Failed: {str(e)}")
        return False