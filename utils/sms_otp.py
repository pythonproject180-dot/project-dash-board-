"""SMS OTP Gateway for Hamro Hospital — Nepal SMS providers integration.
Supports:
1. SMS gateway API (e.g., Sparrow SMS, Vasani, Hamro SMS) 
2. Twilio (international fallback)
3. Console/Simulated mode (for development/testing — shows OTP on screen)

In production, set SMS_GATEWAY environment variable to 'sparrow', 'vasani', or 'twilio'
and configure the respective API credentials.
"""
import os
import random
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SMS_GATEWAY = os.environ.get('SMS_GATEWAY', 'simulated')

# Gateway-specific configs
SPARROW_API_KEY = os.environ.get('SPARROW_API_KEY', '')
SPARROW_API_URL = os.environ.get('SPARROW_API_URL', 'https://api.sparrowsms.com/v2/sms/')
VASANI_API_KEY = os.environ.get('VASANI_API_KEY', '')
VASANI_API_URL = os.environ.get('VASANI_API_URL', 'https://vasani.com.np/api/send_sms')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', '5'))


def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    return str(random.randint(10**(length-1), 10**length - 1))


def send_sms_otp(phone_number, otp, purpose='verification'):
    """Send OTP via SMS to the given phone number.
    
    Returns dict: {'success': bool, 'message': str, 'gateway': str, 'otp': str}
    In simulated mode, the OTP is returned in the response for display.
    """
    message_text = f"Hamro Hospital: Your OTP for {purpose} is {otp}. Valid for {OTP_EXPIRY_MINUTES} minutes. Do not share this code."

    if SMS_GATEWAY == 'sparrow' and SPARROW_API_KEY:
        try:
            import requests
            payload = {
                'token': SPARROW_API_KEY,
                'to': phone_number,
                'text': message_text,
            }
            r = requests.post(SPARROW_API_URL, data=payload, timeout=10)
            if r.status_code == 200:
                logger.info(f'Sparrow SMS OTP sent to {phone_number}')
                return {'success': True, 'message': 'OTP sent via Sparrow SMS', 'gateway': 'sparrow', 'otp': otp}
            else:
                logger.warning(f'Sparrow SMS failed: {r.status_code}')
                return {'success': False, 'message': f'SMS gateway error: {r.status_code}', 'gateway': 'sparrow', 'otp': otp}
        except Exception as e:
            logger.error(f'Sparrow SMS exception: {e}')
            return {'success': False, 'message': str(e), 'gateway': 'sparrow', 'otp': otp}

    elif SMS_GATEWAY == 'vasani' and VASANI_API_KEY:
        try:
            import requests
            payload = {
                'api_key': VASANI_API_KEY,
                'phone': phone_number,
                'message': message_text,
            }
            r = requests.post(VASANI_API_URL, data=payload, timeout=10)
            if r.status_code == 200:
                logger.info(f'Vasani SMS OTP sent to {phone_number}')
                return {'success': True, 'message': 'OTP sent via Vasani SMS', 'gateway': 'vasani', 'otp': otp}
            else:
                logger.warning(f'Vasani SMS failed: {r.status_code}')
                return {'success': False, 'message': f'SMS gateway error: {r.status_code}', 'gateway': 'vasani', 'otp': otp}
        except Exception as e:
            logger.error(f'Vasani SMS exception: {e}')
            return {'success': False, 'message': str(e), 'gateway': 'vasani', 'otp': otp}

    elif SMS_GATEWAY == 'twilio' and TWILIO_ACCOUNT_SID:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=message_text,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number,
            )
            logger.info(f'Twilio SMS OTP sent to {phone_number}, SID: {message.sid}')
            return {'success': True, 'message': 'OTP sent via Twilio', 'gateway': 'twilio', 'otp': otp}
        except Exception as e:
            logger.error(f'Twilio exception: {e}')
            return {'success': False, 'message': str(e), 'gateway': 'twilio', 'otp': otp}

    else:
        # Simulated mode — OTP shown on screen for development/testing
        logger.info(f'SIMULATED OTP for {phone_number}: {otp}')
        return {
            'success': True,
            'message': f'Demo OTP: {otp} (SMS gateway not configured — set SMS_GATEWAY env var to sparrow, vasani, or twilio)',
            'gateway': 'simulated',
            'otp': otp,
            'simulated': True,
        }
