# Telegram-бот для проверки статуса проверки проектов


## Описание
Телеграм-бот для оповещения об изменениях статуса проверки выполненных работ - запускает механизм оповещения в ТГ о статусе проверки проектов. 

Реализовано логирование.


## Технологии

- Python 3.7
- python-telegram-bot
- python-dotenv
- requests


## Запуск бота

1. Клонируйте репозиторий и перейдите в него в командной строке:
```bash
  git clone https://github.com/ArnoSimonian/project_status_bot.git
  cd project_status_bot
```

2. Создайте файл ```.env``` с переменными окружения:

- ```PRACTICUM_TOKEN``` - токен API сервиса Практикум.Домашка
- ```TELEGRAM_TOKEN``` - токен Telegram-бота
- ```TELEGRAM_CHAT_ID``` - ID чата адресата оповещения

3. Cоздайте и активируйте виртуальное окружение:

```bash
  python3 -m venv venv
  # Для Linux/macOS:
  source venv/bin/activate
  # Для Windows:
  source venv/Scripts/activate
```

4. Установите зависимости из файла requirements.txt:

```bash
  python3 -m pip install --upgrade pip
  pip install -r requirements.txt
```

5. Запустите скрипт:

```bash
  python3 homework.py
```


## Автор

Арно Симонян [@ArnoSimonian](https://www.github.com/ArnoSimonian)
