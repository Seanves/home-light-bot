"""
This bot provides information about electricity availability
and must run on Android device that is always on charging.
Android only allows access to its API from Android app,
so we need an app that gives access to API and host server.
I use MacroDroid with GET endpoint /power
that responds "true" if phone is charging
"""
import telebot
from collections import deque
from threading import Thread
from time import time, sleep
import requests
from telebot import types
import datetime
import json


last_action_time = None
electricity_on = None

with open('config.json') as file:
    config = json.load(file)

bot = telebot.TeleBot(config.get("BOT_TOKEN"))
local_server_address = "http://localhost:8080"
chat_ids = set()
messages_queue :deque[str] = deque()


def constant_check():
    global electricity_on, last_action_time

    while True:
        new_state = is_electricity_on()

        if electricity_on != new_state and new_state is not None:

            time_passed = format_time(time() - last_action_time)
            action_word = "увімкнули" if new_state else "вимкнули"
            emoji = "💡" if new_state else "🚫"

            messages_queue.append(f"{emoji} електроенергію {action_word} після {time_passed} в {time_now()}")

            electricity_on = new_state
            last_action_time = time()
            
        try:
            while len(messages_queue) > 0:
                message = messages_queue[0]
                for id in chat_ids:
                    bot.send_message(id, message)
                messages_queue.popleft()
        except:
            print("failed to send message")

        sleep(5)


def is_electricity_on():
    try:
        response = requests.get(local_server_address + "/power")
        response.raise_for_status()
        response_text = response.text.strip().lower()
        return response_text == 'true'
    except Exception as e:
        print(f"Exception in is_electricity_on(): {e}")
        return None

def format_time(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days} day{'' if days == 1 else 's'} {hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{hours:02}:{minutes:02}:{seconds:02}"

def time_now():
    return datetime.datetime.now().strftime('%H:%M %d %B')



@bot.message_handler(commands=['start'])
def start(message: types.Message):
    bot.reply_to(message, f"Привіт {message.from_user.first_name} 😊")
    chat_ids.add(message.chat.id)


@bot.message_handler(commands=['check'])
def check(message: types.Message):
    time_passed = format_time( time() - last_action_time )
    on = is_electricity_on()

    if on is None:
        bot.reply_to(message, f'‼ none. Помилка локального серверу')
        return

    if on:
        bot.reply_to(message, f'💡 електроенергія вже є {time_passed}')
    else:
        bot.reply_to(message, f'🚫 електроенергії немає {time_passed}')



def main():
    global last_action_time, electricity_on
    last_action_time = time()
    electricity_on = is_electricity_on()

    Thread(target=constant_check).start()

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"bot.polling() exception: {e}")
            sleep(15)


if __name__ == '__main__':
    main()
