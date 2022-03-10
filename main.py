import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tradingview_ta import TA_Handler


def calculator(coin, summ, coin_dict):
    for ticket, price in coin_dict.items():
        total_summ = round((summ * price), 2)
        print(summ, coin, '=', total_summ, ticket)


# Курс plex в mine по explorer
mp_driver = webdriver.Chrome()
mp_driver.get("https://explorer.mineplex.io/")
plex_mine_price = float(mp_driver.find_element(By.CLASS_NAME, value='Header').text)
mp_driver.quit()
print(plex_mine_price)


# Курс plex в usdt на CoinGecko
coingecko = requests.get('https://www.coingecko.com/ru/%D0%9A%D1%80%D0%B8%D0%BF%D1%82%D0%BE%D0%B2%D0%B0%D0%BB%D1%8E%D1%82%D1%8B/plex/usd#panel')
plex_coingecko = BeautifulSoup(coingecko.content, "lxml")
plex_usdt_price = float(plex_coingecko.find('span', 'no-wrap').text[1:].replace(',', '.'))
print(plex_usdt_price)

# Курс usdt в рублях на Binance
usdt_rub_tv = TA_Handler(
    symbol='USDTRUB',
    screener='crypto',
    exchange='BINANCE',
    interval='1m',)
usdt_rub_price = usdt_rub_tv.get_analysis().indicators['close']
print(usdt_rub_price)

# Для калькулятора plex
plex_dict = {
    'mine': plex_mine_price,
    'usdt': plex_usdt_price,
    'rub': (plex_usdt_price * usdt_rub_price)
}
mine_dict = {
    'plex': (1 / plex_mine_price),
    'usdt': (plex_usdt_price / plex_mine_price),
    'rub': (plex_usdt_price * usdt_rub_price / plex_mine_price)
}
usdt_dict = {
    'plex': (1 / plex_usdt_price),
    'mine': (plex_mine_price / plex_usdt_price),
    'rub': usdt_rub_price
}
rub_dict = {
    'plex': (1 / plex_dict.get('rub')),
    'mine': (1 / mine_dict.get('rub')),
    'usdt': (1 / usdt_rub_price)
}

print(calculator('rub', 2000, rub_dict))
# print(plex_dict)
# print(mine_dict)
# print(usdt_dict)
# print(rub_dict)


