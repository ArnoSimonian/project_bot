class CheckOutProjectException(Exception):
    """Базовое исключение проекта."""


class JsonException(CheckOutProjectException):
    """Исключение при ошибке метода json()."""


class HTTPException(CheckOutProjectException):
    """Исключение при получении HTTP ответа."""


class KeyException(CheckOutProjectException):
    """Исключение при отсутствии необязательных ключей словаря в ответе API."""

class YandexAPIRequestError(CheckOutProjectException):
    """Ошибка ответа сервера при обработке запроса Yandex API."""