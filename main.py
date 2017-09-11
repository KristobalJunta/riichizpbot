# _*_ coding: utf-8 _*_

from bs4 import BeautifulSoup
from config import config
import telebot
import requests


def parse_data():
    parse_url = 'http://stat.candyrate.com.ua/'
    user_agent = {'User-agent': 'Mozilla/5.0'}
    stats = requests.get(parse_url, headers=user_agent).content.decode('utf-8')
    print(stats)

    if stats:
        cache = open('cache.txt', 'w')
        cache.write(stats)
        cache.close()

    soup = BeautifulSoup(stats, 'html.parser')

    table = soup.find_all('table')
    if table:
        table = table[0]
    else:
        raise Exception('Rating table not found')

    keys = ['place', 'name', 'rating', 'place_avg', 'games', 'points', 'max', 'club']

    data = list()

    for row in table.tbody.find_all('tr'):
        raw_row_data = [x.contents[0] for x in row.find_all('td')]
        row_data = dict(zip(keys, raw_row_data))
        row_data['name'] = row.a.contents[0]
        data.append(row_data)

    return data


def form_row(row_data):
    result = '{} *{}*: рейтинг - {}, игр - {}\n'.format(
        (row_data['place']+'.').ljust(3, ' '),
        row_data['name'],
        row_data['rating'],
        row_data['games'],
    )
    return result


def form_table(table_data):
    result = []
    for row_data in table_data:
        result.append(form_row(row_data))
    return ''.join(result)


bot = telebot.TeleBot(config.get('telegram-token'))


@bot.message_handler(commands=['start'])
def handle_start(message):
    response = 'Добро пожаловать.'
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['help'])
def handle_help(message):
    response = ''.join([
        'Это бот, сделанный для клуба "Ламповый Север"\n',
        'Пока что он умеет только показывать стату - используй команды\n',
        '/stats\n/stats nick'
    ])
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['stats'])
def handle_stats(message):
    bot.send_chat_action(message.chat.id, 'typing')
    args = message.text.strip().split()
    stats = parse_data()

    if len(args) > 1:
        nick = args[1]
        row = [x for x in stats if x['name'] == nick]
        response = form_row(row[0]) if row else 'Такого игрока в таблице нет.'
    else:
        response = form_table(stats)

    response += '\n[таблица](http://stat.candyrate.com.ua/)'
    bot.send_message(message.chat.id, response, parse_mode='Markdown')


bot.polling(none_stop=True, interval=0)
