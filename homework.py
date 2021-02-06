import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = os.getenv('BASE_URL')
OK_MSG = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
NG_MSG = 'К сожалению в работе нашлись ошибки.'

logging.basicConfig(
    level=logging.DEBUG,
    filename='api_sp1_bot.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')

    if homework.get('status') == 'rejected':
        verdict = NG_MSG
    else:
        verdict = OK_MSG

    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(
            url=BASE_URL,
            timeout=5,
            headers=headers,
            params=params
        )
    except requests.exceptions.HTTPError as errh:
        msg = f"Http Error: {errh}"
        logging.error(msg)
        print(msg)
    except requests.exceptions.ConnectionError as errc:
        msg = f'Error Connecting:{errc}'
        logging.error(msg)
        print(msg)
    except requests.exceptions.Timeout as errt:
        msg = f'Timeout Error: {errt}'
        logging.error(msg)
        print(msg)
    except requests.exceptions.RequestException as err:
        msg = f'Что-то пошло не так {err}'
        logging.error(msg)
        print(msg)

    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Сообщение в телеграмм чат отправлено')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Телеграмм бот запущен')

    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client=bot)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(1800)

        except Exception as e:
            msg = f'Бот столкнулся с ошибкой: {e}'
            print(msg)
            send_message(message=msg, bot_client=bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
