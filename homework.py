import logging
import os
import sys
import time
from http import HTTPStatus
from json.decoder import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (ConnectionException, HTTPException, JsonException,
                        SomeDateError, YandexAPIRequestError)

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
    missing_tokens = [token for token in TOKENS_NAMES
                      if not globals().get(token)]
    if missing_tokens:
        logger.critical(f'Отсутствуют переменные окружения: '
                        f'{", ".join(missing_tokens)}!')
        raise SystemExit
    logger.debug("Переменные окружения доступны.")


def send_message(bot, message):
    """Отправляет сообщение со статусом проверки работы в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error(f'Не удалось отправить сообщение: {error}')
    else:
        logger.debug("Сообщение о статусе проверки работы успешно отправено.")


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса, возвращает ответ API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            code, text = response.status_code, response.text
            error = f"Код ответа: {code}, сообщение об ошибке: {text}."
            raise HTTPException(f'{error}')
        return response.json()
    except requests.RequestException as error:
        raise ConnectionException(
            f'Ошибка подключения: {error}'
        ) or YandexAPIRequestError(
            f'Ошибка ответа сервера: {error}'
        )
    except JSONDecodeError as error:
        raise JsonException(
            f'{error}: API вернул недопустимый json. '
            f'Ответ: {response.text}.'
        )


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
        raise SomeDateError(
            "В ответе API нет ключа current_date. "
            "Работа программы может быть продолжена."
        )
    if not isinstance(response['current_date'], int):
        raise SomeDateError(
            "Неожиданный тип ответа от API: "
            "Ключ current_date должен быть целым числом."
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            "Невалидный тип ответа от API: "
            "Ключ 'homeworks' должен быть списком."
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

        except SomeDateError as error:
            err_message = f'{error}'
            logger.error(f'{err_message}')

        except Exception as error:
            err_message = f'Сбой в работе программы. {error}'
            logger.error(f'{err_message}')
            if err_message != prev_message:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=err_message)
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
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Принудительная остановка программы.')
