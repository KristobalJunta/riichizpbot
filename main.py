# _*_ coding: utf-8 _*_

from bs4 import BeautifulSoup
from config import config
import telebot
import requests


def parse_data():
    user_agent = {'User-agent': 'Mozilla/5.0'}
    stats = requests.get(config.get('url'), headers=user_agent).content.decode('utf-8')

    if stats:
        with open('cache.txt', 'w') as cache:
            cache.write(stats)

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
        '/stats\n/stats NICK[, SECOND NICK, ...]'
    ])
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['stats'])
def handle_stats(message):
    bot.send_chat_action(message.chat.id, 'typing')
    args = message.text.strip().split()
    stats = parse_data()

    if len(args) > 1:
        nicknames = [n.strip().lower() for n in ''.join(args[1:]).split(',')]
        rows = [x for x in stats if x['name'].lower() in nicknames]
        if len(rows) == 0:
            player = 'Игрока' if len(nicknames) == 1 else 'Игроков'
            response = '{} {} в таблице нет.'.format(player, args[1:])
        else:
            response = ''
            for row in rows:
                response += form_row(row)
    else:
        response = form_table(stats[0:5])

    response += '\n[таблица](http://stat.candyrate.com.ua/)'
    bot.send_message(message.chat.id, response, parse_mode='Markdown')


bot.polling(none_stop=True, interval=0)
