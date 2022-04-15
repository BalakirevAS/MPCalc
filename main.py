import time
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from tradingview_ta import TA_Handler
import telebot
from telebot import types
import os
from flask import Flask, request



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
            'MINE': price.get('PLEX').get('mine'),
            'USDT': price.get('PLEX').get('usdt'),
            'RUB': price.get('PLEX').get('rub'),
            'KZT': price.get('PLEX').get('kzt')
        },
        '1 MINE': {
            'USDT': price.get('MINE').get('usdt'),
            'RUB': price.get('MINE').get('rub'),
            'KZT': price.get('MINE').get('kzt')
        },
        '1 USDT': {
            'RUB': price.get('USDT').get('rub'),
            'KZT': price.get('USDT').get('kzt')
        }
    }
    return exch_rate


def parsing_web():
    # Курс plex в mine по explorer
    # mp_driver = webdriver.Chrome()
    GOOGLE_CHROME_BIN = '/app/.apt/usr/bin/google-chrome'
    CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
    options = Options()
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--headless")
    options.add_argument("--example-flag")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    service = Service(str(os.environ.get('CHROMEDRIVER_PATH')))
    mp_driver = webdriver.Chrome(service=service, options=options)
    mp_driver.get("https://explorer.mineplex.io/")
    time.sleep(1)
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

    # Курс KZT (Тенге) к доллару
    usd_kzt_tv = TA_Handler(
        symbol='USDKZT',
        screener='forex',
        exchange='FX_IDC',
        interval='1m', )
    usd_kzt_price = usd_kzt_tv.get_analysis().indicators['close']

    price_dict = {
        'PLEX': {
            'mine': plex_mine_price,
            'usdt': plex_usdt_price,
            'rub': (plex_usdt_price * usdt_rub_price),
            'kzt': (plex_usdt_price * usd_kzt_price)
        },
        'MINE': {
            'plex': (1 / plex_mine_price),
            'usdt': (plex_usdt_price / plex_mine_price),
            'rub': (plex_usdt_price * usdt_rub_price / plex_mine_price),
            'kzt': (plex_usdt_price * usd_kzt_price / plex_mine_price)
        },
        'USDT': {
            'plex': (1 / plex_usdt_price),
            'mine': (plex_mine_price / plex_usdt_price),
            'rub': usdt_rub_price,
            'kzt': usd_kzt_price
        },
        'RUB': {
            'plex': (1 / plex_usdt_price / usdt_rub_price),
            'mine': (plex_mine_price / plex_usdt_price / usdt_rub_price),
            'usdt': (1 / usdt_rub_price)
        },
        'KZT': {
            'plex': (1 / plex_usdt_price / usd_kzt_price),
            'mine': (plex_mine_price / plex_usdt_price / usd_kzt_price),
            'usdt': (1 / usd_kzt_price)
        }
    }
    return price_dict


price_t = dict()
msg_list = dict()

TOKEN = '5110887553:AAE1lDFwWu6axLhk999LtUcjLgGwo8lFFbk'
MPCalc_bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@MPCalc_bot.message_handler(commands=['start'])
def greeting_msg(message):
    MPCalc_bot.send_message(message.chat.id, 'Привет, {0.first_name}! \nЯ MPCalc - MinePlex Calculator!'
                                             ' Я могу показать актуальные курсы Plex, Mine, USDT, '
                                             'а также посчитать общую сумму при конвертации!'
                            .format(message.from_user))
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b_rate = types.KeyboardButton('Курсы валют')
    b_calc = types.KeyboardButton('Калькулятор')
    menu.add(b_rate, b_calc)
    msg = MPCalc_bot.send_message(message.chat.id,
                                  'Для начала работы выберите одну из функций'.format(message.from_user),
                                  reply_markup=menu)
    MPCalc_bot.register_next_step_handler(msg, menu_msg)


@MPCalc_bot.message_handler(commands=['text'])
def menu_msg(message):
    if message.text == 'Калькулятор':
        tickets = types.ReplyKeyboardMarkup(resize_keyboard=True)
        b_plex = types.KeyboardButton('PLEX')
        b_mine = types.KeyboardButton('MINE')
        b_usdt = types.KeyboardButton('USDT')
        b_rub = types.KeyboardButton('RUB')
        b_kzt = types.KeyboardButton('KZT')
        back = types.KeyboardButton('Курсы валют')
        tickets.add(b_plex, b_mine, b_usdt, b_rub, b_kzt, back)
        msg = MPCalc_bot.send_message(message.chat.id, text='Выберите тикет', reply_markup=tickets)
        MPCalc_bot.register_next_step_handler(msg, ticket_msg)
    elif message.text == 'Курсы валют':
        MPCalc_bot.send_message(message.chat.id, 'Подождите, собираю информацию...')
        exch_rate = exchange_rate()
        for i, j in exch_rate.items():
            for k, l in j.items():
                MPCalc_bot.send_message(message.chat.id, f'{i} = {round(l, 4)} {k}.')
        msg = MPCalc_bot.send_message(message.chat.id, 'Источники: Explorer, CoinGecko, Binance.')
        MPCalc_bot.register_next_step_handler(msg, menu_msg)


def ticket_msg(message):
    if message.text == 'Курсы валют':
        menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        b_rate = types.KeyboardButton('Курсы валют')
        b_calc = types.KeyboardButton('Калькулятор')
        menu.add(b_rate, b_calc)
        MPCalc_bot.send_message(message.chat.id, 'Подождите, собираю информацию...')
        exch_rate = exchange_rate()
        for i, j in exch_rate.items():
            for k, l in j.items():
                MPCalc_bot.send_message(message.chat.id, f'{i} = {round(l, 4)} {k}.')
        msg = MPCalc_bot.send_message(message.chat.id, 'Источники: Explorer, CoinGecko, Binance.', reply_markup=menu)
        MPCalc_bot.register_next_step_handler(msg, menu_msg)
    else:
        msg_list['ticket'] = message.text
        msg = MPCalc_bot.send_message(message.chat.id, 'Введите целое количество для расчёта (без точек и запятых):')
        MPCalc_bot.register_next_step_handler(msg, save_summ)


def save_summ(message):
    chek_msg = message.text
    if chek_msg.isdigit():
        MPCalc_bot.send_message(message.chat.id, 'Подождите, сейчас посчитаю...')
        price_t = parsing_web()
        msg_list['summ'] = int(message.text)
        answer = calculator(msg_list.get('summ'), price_t.get(msg_list.get('ticket')))
        for i, j in answer.items():
            MPCalc_bot.send_message(message.chat.id, '{} {} = {} {}'.format(msg_list['summ'], msg_list['ticket'], j, i))
        MPCalc_bot.send_message(message.chat.id, 'Если бот не отвечает, введите повторно команду /start.'
                                                 '\nВсе предложения и пожелания по работе бота'
                                                 ' вы можете написать мне в личку @ASBalakirev.'
                                                 '\nБот бесплатный, но для поддержания хостинга и дальнейшего совершенствования, '
                                                 'или если захотите просто отблагодарить за работу, приму mine или plex.'
                                                 '\nМой ID: 452516701.')
        msg = MPCalc_bot.send_message(message.chat.id, 'Выберите действие:')
        MPCalc_bot.register_next_step_handler(msg, ticket_msg)
    else:
        MPCalc_bot.send_message(message.chat.id, 'Введено некорректное значение!')
        msg = MPCalc_bot.send_message(message.chat.id, 'Введите целое количество для расчёта (без точек и запятых):')
        MPCalc_bot.register_next_step_handler(msg, save_summ)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    MPCalc_bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    MPCalc_bot.remove_webhook()
    MPCalc_bot.set_webhook(url='https://mp-calulator.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))


MPCalc_bot.infinity_polling()
