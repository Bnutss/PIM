import requests


def send_telegram_message(message: str):
    bot_token = '6847243024:AAH4tnawb0eAZVNugjBu5d08rbzm-72V18c'
    chat_id = '-1002180391121'
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    response = requests.post(url, data=payload)

    return response.json()
