# Django-Telegram-Bot
Django + Python-Telegram-Bot

System : Ubuntu
Python : 3.10.12

sudo apt update

sudo apt install pkg-config

sudo apt install libmysqlclient-dev


## Dependencies

```sh
pip install -r requirements.txt

python3 manage.py makemigrations
python3 manage.py migrate
```

## Running

If you want to run a personal trading bot

```sh
python3 main_bot.py
```

or want to run a group trading bot

```sh
python3 trading_bot.py
```