import logging
import os
import sys
import time

from http import HTTPStatus
from json.decoder import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (HTTPException, JsonException, TelegramMessageError,
                        YandexAPIRequestError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)

TOKENS_NAMES = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for name in TOKENS_NAMES:
        if not globals().get(name):
            logger.critical(f'Отсутствует переменная окружения {name}!')
            raise SystemExit
        logger.debug("Переменные окружения доступны.")


def send_message(bot, message):
    """Отправляет сообщение со статусом проверки работы в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug("Сообщение о статусе проверки работы успешно отправено.")
    except telegram.error.TelegramError as error:
        logger.error(f'Не удалось отправить сообщение: {error}')
        raise TelegramMessageError(
            f'Не удалось отправить сообщение: {error}'
        )


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса, возвращает ответ API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise YandexAPIRequestError(
            f'Ошибка ответа сервера: {error}'
        )
    if response.status_code != HTTPStatus.OK:
        code, text = response.status_code, response.text
        details = f"Код ответа: {code}, сообщение об ошибке: {text}."
        raise HTTPException(f'{details}')
    try:
        response = response.json()
    except JSONDecodeError:
        raise JsonException(
            "API вернул недопустимый json. "
            f'Ответ: {response.text}.'
        )
    return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            "Невалидный тип ответа от API: "
            "Ответ должен быть словарем."
        )
    if 'homeworks' not in response:
        raise KeyError(
            "Невалидный формат ответа от API: "
            "Отсутствует необходимый ключ 'homeworks'."
        )
    if 'current_date' not in response:
        raise KeyError(
            "Невалидный формат ответа от API: "
            "Отсутствует необходимый ключ 'current_date'."
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            "Невалидный тип ответа от API: "
            "Ключ 'homeworks' должен быть списком.",
        )
    return response['homeworks']


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    Возвращает подготовленную для отправки в Telegram строку со статусом.
    """
    if 'homework_name' not in homework:
        raise KeyError(
            "Невалидный формат ответа от API: "
            "Отсутствует необходимый ключ 'homework_name'."
        )
    if 'status' not in homework:
        raise KeyError(
            "Невалидный формат ответа от API: "
            "Отсутствует необходимый ключ 'status'."
        )
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы: {homework_status}.')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    prev_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = response['current_date']
            if response['homeworks']:
                homework = response['homeworks'][0]
                message = parse_status(homework)
                send_message(bot, message)
                logger.debug(f'Бот отправил сообщение об изменении '
                             f'статуса работы: {message}')
            else:
                message = "Статус не изменился."
                logger.debug(f'{message} Сообщение не отправлено.')

        except Exception as error:
            err_message = f'Сбой в работе программы: {error}'
            if err_message != prev_message:
                send_message(bot, err_message)
                logger.error(f'Бот отправил сообщение о сбое в работе '
                             f'программы {err_message}')
                prev_message = err_message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s, %(name)s, %(levelname)s, %(message)s,'
            '%(funcName)s, %(lineno)d'
        ),
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler('my_logger.log', mode='a', encoding='utf-8')
        ]
    )
    main()
