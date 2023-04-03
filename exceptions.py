class CheckOutProjectException(Exception):
    """Базовое исключение проекта."""


class JsonException(CheckOutProjectException):
    """Исключение при ошибке метода json()."""


class HTTPException(CheckOutProjectException):
    """Исключение при получении HTTP ответа."""


class TelegramMessageError(CheckOutProjectException):
    """Ошибка неудачной попытки отправить сообщение в Telegram."""


class YandexAPIRequestError(CheckOutProjectException):
    """Ошибка ответа сервера при обработке запроса Yandex API."""