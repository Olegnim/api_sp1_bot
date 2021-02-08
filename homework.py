import json
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
METHOD_API_1 = 'homework_statuses/'
BASE_URL = 'https://praktikum.yandex.ru/api/user_api/'
MSG_APPROVED = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
MSG_REVIEWING = 'Работа пока находится на проверке.'
MSG_REJECTED = 'К сожалению в работе нашлись ошибки.'

logging.basicConfig(
    level=logging.DEBUG,
    filename='api_sp1_bot.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    status_verdict = {
        'reviewing': MSG_REVIEWING,
        'approved': MSG_APPROVED,
        'rejected': MSG_REJECTED,
    }
    err_return = {}
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error('Ошибка получения названия работы')
        return err_return
    status = homework.get('status')
    if status_verdict.get(status) is None:
        if status != '':
            logging.error('Ошибка! Cтатус не распознан!')
            return err_return
        logging.error('Ошибка! Нет такого статуса')
        return err_return
    verdict = status_verdict.get(status)
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    err_return = {}
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    API_URL = BASE_URL + '{}'.format(METHOD_API_1)
    try:
        homework_statuses = requests.get(
            url=API_URL,
            timeout=30,
            headers=headers,
            params=params
        )
    except requests.exceptions.HTTPError as errh:
        logging.exception(f"Http Error: {errh}")
        return err_return
    except requests.exceptions.ConnectionError as errc:
        logging.exception(f'Error Connecting: {errc}')
        return err_return
    except requests.exceptions.Timeout as errt:
        logging.exception(f'Timeout Error: {errt}')
        return err_return
    except requests.exceptions.RequestException as err:
        logging.exception(f'Что-то пошло не так {err}')
        return err_return
    except json.JSONDecodeError:
        logging.exception('Ошибка сериализации JSON!')
        return err_return
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Сообщение в телеграмм чат отправлено')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except Exception:
        logging.error('Ошибка инициализации телеграмм бота!')
    logging.debug('Телеграмм бот запущен')

    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework == dict():
                msg = 'Ошибка! Нет данных!'
                logging.error(msg)
                send_message(message=msg, bot_client=bot)
            if new_homework.get('homeworks'):
                new_hw = new_homework.get('homeworks')[0]
                parse_hw_status = parse_homework_status(new_hw)
                if parse_hw_status == dict():
                    send_message('Ошибка получения статуса!', bot_client=bot)
                else:
                    send_message(parse_hw_status, bot_client=bot)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(1800)

        except Exception as e:
            msg = f'Бот столкнулся с ошибкой: {e}'
            logging.error(msg)
            send_message(message=msg, bot_client=bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
