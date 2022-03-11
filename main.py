import time
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tradingview_ta import TA_Handler
import telebot
from telebot import types


def calculator(summ, coin_dict):  # Калькулятор стоимости от общей суммы
    answer = {}
    for ticket, price in coin_dict.items():
        total_summ = round((summ * price), 2)
        answer[ticket] = total_summ
    return answer

def exchange_rate():  # Курс монет
    price = parsing_web()
    exch_rate = {
        '1 PLEX': {
            'MINE': price.get('plex_dict').get('mine'),
            'USDT': price.get('plex_dict').get('usdt'),
            'RUB': price.get('plex_dict').get('rub')
        },
        '1 MINE': {
            'USDT': price.get('mine_dict').get('usdt'),
            'RUB': price.get('mine_dict').get('rub')
        },
        '1 USDT': {
            'RUB': price.get('usdt_dict').get('rub')
        }
    }
    return exch_rate

def parsing_web():
        # Курс plex в mine по explorer
    mp_driver = webdriver.Chrome()
    mp_driver.get("https://explorer.mineplex.io/")
    time.sleep(3)
    plex_mine_price = float(mp_driver.find_element(By.CLASS_NAME, value='Header').text)
    mp_driver.quit()

        # Курс plex в usdt на CoinGecko
    coingecko = requests.get(
        'https://www.coingecko.com/ru/%D0%9A%D1%80%D0%B8%D0%BF%D1%82%D0%BE%D0%B2%D0%B0%D0%BB%D1%8E%D1%82%D1%8B/plex/usd#panel')
    plex_coingecko = BeautifulSoup(coingecko.content, "lxml")
    plex_usdt_price = float(plex_coingecko.find('span', 'no-wrap').text[1:].replace(',', '.'))

       # Курс usdt в рублях на Binance
    usdt_rub_tv = TA_Handler(
        symbol='USDTRUB',
        screener='crypto',
        exchange='BINANCE',
        interval='1m', )
    usdt_rub_price = usdt_rub_tv.get_analysis().indicators['close']

    price_dict = {
        'plex_dict': {
            'mine': plex_mine_price,
            'usdt': plex_usdt_price,
            'rub': (plex_usdt_price * usdt_rub_price)
        },
        'mine_dict': {
            'plex': (1 / plex_mine_price),
            'usdt': (plex_usdt_price / plex_mine_price),
            'rub': (plex_usdt_price * usdt_rub_price / plex_mine_price)
        },
        'usdt_dict': {
            'plex': (1 / plex_usdt_price),
            'mine': (plex_mine_price / plex_usdt_price),
            'rub': usdt_rub_price
        },
        'rub_dict': {
            'plex': (1 / (plex_usdt_price / usdt_rub_price)),
            'mine': (plex_mine_price / plex_usdt_price / usdt_rub_price),
            'usdt': (1 / usdt_rub_price)
        }
    }
    return price_dict



# MPCalc_bot = telebot.TeleBot('5110887553:AAElcOlMkHepEkas3ip15IWZL6iZCupLC7U')
# @MPCalc_bot.message_handler(commands=['start'])
# def get_text_messages(message):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     item1 = types.KeyboardButton("RUB")
#     markup.add(item1)
#     MPCalc_bot.send_message(message.chat.id, 'Привет, {0.first_name}!'.format(message.from_user), reply_markup=markup)
#
#
# # @MPCalc_bot.message_handler(commands=['button'])
# # def button_message(message):
# #
# #     # MPCalc_bot.send_message(message.chat.id, 'Калькулятор', reply_markup=markup)
#
#
# @MPCalc_bot.message_handler(content_types='text')
# def message_reply(message):
#     if message.text == "RUB":
#         msgprice = MPCalc_bot.send_message(message.chat.id, 'Введите количество:')
#         MPCalc_bot.register_next_step_handler(msgprice, step_set_price)

# MPCalc_bot.infinity_polling()

calculator('rub', 2000, rub_dict)
