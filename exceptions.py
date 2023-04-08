class CheckOutProjectException(Exception):
    """Базовое исключение проекта."""


class ConnectionException(CheckOutProjectException):
    """Исключение при ошибке подключения."""

class JsonException(CheckOutProjectException):
    """Исключение при ошибке метода json()."""


class HTTPException(CheckOutProjectException):
    """Исключение при получении HTTP ответа."""


class YandexAPIRequestError(CheckOutProjectException):
    """Ошибка ответа сервера при обработке запроса Yandex API."""