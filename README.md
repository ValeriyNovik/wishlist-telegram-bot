# Telegram Wishlist Bot
Учебный pet-проект: 
Telegram-бот для создания списка желаний и просмотра желаний друзей в рамках общих групп.

## Возможности
- Создание профиля пользователя, привязанного к Telegram
- Пошаговое добавление желаний (описание - ссылка - цена)
- Просмотр собственных желаний
- Группы с кодом приглашения
- Просмотр желаний других пользователей только в общих группах

## Используемые программы и библиотеки
- Python 3
- aiogram 3
- SQLite
- Git
- Linux (Ubuntu)

## Будущие обновления 
- Возможность удалить группу

## Запуск проекта локально (Ubuntu)

- sudo apt install -y python3 python3-venv python3-pip sqlite3
- git clone https://github.com/ValeriyNovik/wishlist-telegram-bot
- cd ~/wishlist_bot

- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

# Создать файл .env на основе .env.example
- cp .env.example .env

# Указать токен Telegram-бота
- nano .env

# Запуск программы
- python3 bot.py
