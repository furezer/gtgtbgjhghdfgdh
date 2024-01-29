from aiogram import types
from country import COUNTRY
from city import CITY
from period import PERIOD
from config import PROXY_KEY
import requests
import sqlite3

async def menu_keyboard(us_id):
	keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=2)
	btn = [
	types.KeyboardButton(text="📲 Купить"),
	types.KeyboardButton(text="🖥 Профиль"),
	types.KeyboardButton(text="ℹ️ Информация")
	]
	admin = types.KeyboardButton(text='Админка')
	keyboard.add(*btn)
	from functions import GET_ADMIN_STATUS
	if await GET_ADMIN_STATUS(us_id) == 1:
		keyboard.add(admin if await GET_ADMIN_STATUS(us_id) == 1 else [])
	return keyboard

async def proxy_main_keyboard():
	keyboard = types.InlineKeyboardMarkup(row_width=2)
	keyboard.add(*[
		types.InlineKeyboardButton(text='🛒 Купить', callback_data='get_proxy_type')
		])
	return keyboard

async def proxy_profile_keyboard():
	keyboard = types.InlineKeyboardMarkup(row_width=2)
	keyboard.add(*[
		types.InlineKeyboardButton(text="💳 Пополнить баланс", callback_data='deposit'),
		types.InlineKeyboardButton(text='🗂 Мои прокси', callback_data='my_proxy')
		])
	return keyboard

async def deposit_keyboard():
	keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
	conn = sqlite3.connect('db.db', check_same_thread=False)
	cursor = conn.cursor()
	row = cursor.execute('SELECT * FROM settings').fetchone()
	if row[4] and row[5]:
		keyboard.add(
			types.KeyboardButton(text='💳 QIWI/CARD'),
			types.KeyboardButton(text='💜 ЮKassa'),
            types.KeyboardButton(text='💜 Lava')
		)
	elif row[4]:
		keyboard.add(
			types.KeyboardButton(text='💳 QIWI/CARD'))
	elif row[5]:
		keyboard.add(
            types.KeyboardButton(text='💜 ЮKassa'))
	keyboard.add(types.KeyboardButton(text='Меню'))
	return keyboard

async def get_proxy_type_keyboard():
	keyboard = types.InlineKeyboardMarkup(row_width=2)
	keyboard.add(*[
		types.InlineKeyboardButton(text='🥷 Private IPv4', callback_data='set_type|dedicated|4'),
		types.InlineKeyboardButton(text='👨‍👨‍👧‍👦 Shared IPv4', callback_data='set_type|shared|4'),
		types.InlineKeyboardButton(text='🥷 Private IPv6', callback_data='set_type|dedicated|6')
		])
	return keyboard

async def get_country_keyboard(i):
	keyboard = types.InlineKeyboardMarkup(row_width=3)
	btn = []
	navigation = []
	i=int(i)
	stop = i+9
	num = 0
	for ids in COUNTRY:
		num +=1
		if i < num:
			if i < stop:
				country_name = COUNTRY.get(ids)
				btn.append(types.InlineKeyboardMarkup(text=country_name, callback_data =f'set_country_|{ids}|{country_name}'))
				i +=1
	print(len(btn))
	keyboard.add(*btn)
	if i > 9:
		navigation.append(types.InlineKeyboardButton(text='◀️', callback_data=f'next_country|{i-18}'))

	if len(btn) == 9:
		navigation.append(types.InlineKeyboardButton(text='➡️', callback_data=f'next_country|{i}'))
	keyboard.add(*navigation)
	keyboard.add(types.InlineKeyboardButton(text='🔘 Меню', callback_data='get_proxy_type'))
	return keyboard

async def get_city_keyboard(country_code):
	keyboard = types.InlineKeyboardMarkup(row_width = 3)
	URL = f'https://panel.proxyline.net/api/countries/?api_key={PROXY_KEY}'
	r = requests.get(URL)
	dct = r.json()
	btn = []
	for i in dct:
		if i.get('code') == country_code:
			for city in i['cities']:
				print(city['id'])
				btn.append(types.InlineKeyboardButton(text= city['name'], callback_data='set_city_|{0}|{1}'.format(city.get('id'),city.get('name'))))
	keyboard.add(*btn)
	return keyboard

async def get_period_keyboard():
	keyboard = types.InlineKeyboardMarkup(row_width = 3)
	btn = []
	for i in PERIOD:
		btn.append(types.InlineKeyboardButton(text=i, callback_data=f'set_period_{i}'))
	keyboard.add(*btn)
	return keyboard

async def close_message_keyboard():
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(types.InlineKeyboardButton(text='❌ Закрыть', callback_data='delete_message'))
	return keyboard

async def admin_keyboard():
	keyboard = types.ReplyKeyboardMarkup(one_time_keyboard = False, resize_keyboard=True, row_width=2)
	keyboard.add(*[
		types.KeyboardButton(text = 'Сделать рассылку'),
		types.KeyboardButton(text = 'Изменить наценку'),
		types.KeyboardButton(text = 'Выдать баланс')
		])
	keyboard.add(*[
		types.KeyboardButton(text='Включить ЮKassa'),
		types.KeyboardButton(text='Включить QIWI'),
        types.KeyboardButton(text='Включить Lava'),
		types.KeyboardButton(text='Выключить ЮKassa'),
		types.KeyboardButton(text='Выключить QIWI'),
        types.KeyboardButton(text='Выключить Lava')
	])
	keyboard.add(
		types.KeyboardButton(text= 'Меню')
		)
	return keyboard