import sqlite3

import config
from config import *
from aiogram import Bot, Dispatcher, executor, types
from pycbrf.toolbox import ExchangeRates
import datetime
from pyqiwip2p import QiwiP2P
from keyboards import *
from rules import get_rules
from LavaBusiness import AioLava
import random
import requests

bot = Bot(token=BOT_TOKEN, parse_mode='HTML')

async def GET_ADMIN_STATUS(us_id):
	if us_id == ADMIN:
		admin = 1
	else:
		conn = sqlite3.connect('db.db', check_same_thread=False)
		cursor = conn.cursor()
		admin = cursor.execute('SELECT admin FROM users WHERE user_id = (?)', (us_id,)).fetchone()[0]
		conn.close()
	return admin
	
async def CHECK_IN_BASE(us_id):
	conn = sqlite3.connect("db.db", check_same_thread=False)
	cur = conn.cursor()
	in_base = cur.execute('SELECT user_id FROM users WHERE user_id = (?)', (us_id,)).fetchone()
	return in_base

async def DB_GET_BALANCE(us_id):
	conn = sqlite3.connect('db.db', check_same_thread=False)
	cursor = conn.cursor()
	balance = cursor.execute('SELECT balance FROM users WHERE user_id = (?)', (us_id,)).fetchone()[0]
	conn.close()
	return balance

async def DB_GET_NACENKA():
	conn = sqlite3.connect('db.db', check_same_thread=False)
	cursor = conn.cursor()
	nacenka = cursor.execute('SELECT nacenka FROM settings').fetchone()[0]
	conn.close()
	return nacenka

async def menu(us_id):
	await bot.send_photo(chat_id=us_id, photo=MENU_IMAGE, caption= 

f'''

<b>💬 Добро пожаловать!</b>
<b><i>💰 Ваш баланс: {await DB_GET_BALANCE(us_id)} RUB</i></b>

''', reply_markup=await menu_keyboard(us_id))
	#await bot.send_message(chat_id= us_id, text = f'Добро пожаловать!\nВаш баланс: {await DB_GET_BALANCE(us_id)} RUB', reply_markup=await menu_keyboard(us_id))

async def profile(message):
	conn = sqlite3.connect('db.db', check_same_thread = False)
	cursor = conn.cursor()
	row = cursor.execute('SELECT balance, all_buy, all_deposit FROM users WHERE user_id = (?)', (message.from_user.id,)).fetchone()
	await bot.send_photo(chat_id= message.from_user.id, photo=PROFILE_IMAGE, caption=
'''

<b>🥷 Профиль:</b>
➖➖➖➖➖➖➖➖➖➖➖➖

<b>🤖 ID:</b> <code>{0}</code>
<b>💰 Баланс:</b> <i>{1}₽</i> 

<b>🔄 Куплено прокси:</b> <i>{2} шт</i>
<b>💸 Внесено средств:</b> <i>{3}₽</i>		


'''.format(message.from_user.id, row[0], row[1], row[2]), reply_markup=await proxy_profile_keyboard())

async def info(message):
	keyboard = types.InlineKeyboardMarkup(row_width=2)
	keyboard.add(*[
		types.InlineKeyboardButton(text='👨‍💻 Админ', url=ADMIN_LINK),
		types.InlineKeyboardButton(text='🔗 Канал', url=CHANNEL_LINK),
		types.InlineKeyboardButton(text='📖 Правила', callback_data='get_rules')
		])
	await bot.send_photo(chat_id= message.from_user.id, photo=MENU_IMAGE, caption='<b>ℹ️ Информация:</b>', reply_markup=keyboard)

async def adminka(message):
	conn = sqlite3.connect('db.db', check_same_thread = False)
	cursor = conn.cursor()
	row = cursor.execute('SELECT * FROM settings').fetchone()
	all_users = cursor.execute("SELECT COUNT(1) FROM users").fetchone()[0]
	balance = requests.get(f'https://panel.proxyline.net/api/balance/?api_key={PROXY_KEY}').json()['balance']
	balance = await getRates(balance)
	await message.answer(
'''
<b>📊 Статистика бота:</b>
➖➖➖➖➖➖➖➖➖➖➖➖

<i>🙍‍♂️ Количество пользователей: {0} шт
🔏 Куплено прокси: {1} шт
➖➖➖➖➖➖➖➖➖➖➖➖
🏦 Внесено средств: {2}₽
💰 Заработано средств: {3}₽
➖➖➖➖➖➖➖➖➖➖➖➖
➕ Наценка на прокси: {4}₽
🤖 Баланс на proxyline: {5}₽ </i>


'''.format(all_users, row[2], row[1], row[3], row[0], balance), reply_markup = await admin_keyboard())

async def start_photo_rassilka(message, state):
	conn = sqlite3.connect('db.db', check_same_thread = False)
	cursor = conn.cursor()
	users = cursor.execute('SELECT user_id FROM users').fetchall()
	data = await state.get_data()
	text = data['text']
	y = 0
	n = 0
	for user in users:
		try:
			await bot.send_photo(chat_id = user[0], photo=message.photo[-1].file_id, caption = text, reply_markup= await close_message_keyboard())
			y +=1
		except Exception as e:
			n +=1
	await state.finish()
	await bot.send_message(message.from_user.id, text=f'Рассылка завершена!\nОтправлено: {y}\nНе отпралено: {n}', reply_markup = await admin_keyboard())
	conn.close()

async def start_text_rassilka(message, state):
	conn = sqlite3.connect('db.db', check_same_thread = False)
	cursor = conn.cursor()
	users = cursor.execute('SELECT user_id FROM users').fetchall()
	y = 0
	n = 0
	for user in users:
		try:
			await bot.send_message(chat_id = user[0], text=message.text, reply_markup= await close_message_keyboard())
			y +=1
		except Exception as e:
			n +=1
	await state.finish()
	await bot.send_message(message.from_user.id, text=f'Рассылка завершена!\nОтправлено: {y}\nНе отпралено: {n}', reply_markup = await admin_keyboard())
	conn.close()



async def getRates(cost=0):
	try:
		time = datetime.datetime.now().strftime('%Y-%m-%d')
		rates = ExchangeRates(str(time))
		rubles = rates['USD'].value
		price = round(float(rubles)*cost, 2)
		return price
	except Exception as e:
		raise e

async def QIWI_PAY(summa, user_id):
	try:
		#conn = sqlite3.connect('db.db', check_same_thread=False)
		#cursor = conn.cursor()
		#cursor.execute('SELECT QIWI_KEY FROM settings')
		#QIWI_KEY = cursor.fetchone()[0]
		#conn.close()
		qid = user_id + random.randint(1111111, 9999999)
		p2p = QiwiP2P(auth_key=QIWI_KEY)
		new_bill = p2p.bill(bill_id=qid, amount=summa, lifetime=30, comment = "PROXY_BOT")
		keyboard = types.InlineKeyboardMarkup(row_width = 2)
		buttons = [
		types.InlineKeyboardButton(text = "💳 Оплатить", url = new_bill.pay_url),
		types.InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f'CheckQiwi_{qid}'),
		#types.InlineKeyboardButton(text = "🔘 В меню", callback_data = 'menu')
		]
		keyboard.add(*buttons)
		#await bot.send_sticker(chat_id = user_id, sticker='CAACAgIAAxkBAAEEhsdiYVAvtORuUygm70_B1w4CA-9QGAACzRMAAl6zyEvD5PzG428z7yQE', reply_markup= await menu_keyboard(user_id))
		await bot.send_message(chat_id = user_id, text = f'<b><i>💴 Сумма к оплате: {summa} RUB</i></b>', reply_markup = keyboard)
	except Exception as e:
		await bot.send_message(chat_id = ADMIN, text = f'Ошибка пополнения QIWI:\n{e}')
		await menu(user_id)
		await bot.send_message(chat_id = user_id, text ='<b><i>Депозит через QIWI временно недоступно...\nМы уже занимаемся этим вопросом</i></b>')

async def check_qiwi(call):
	pid = call.data[10:]
	p2p = QiwiP2P(auth_key=QIWI_KEY)
	status = p2p.check(bill_id=pid).status
	if status == 'PAID':
		await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)
		amount = p2p.check(bill_id=pid).amount
		conn = sqlite3.connect('db.db', check_same_thread=False)
		cursor = conn.cursor()
		cursor.execute('UPDATE settings SET all_deposits = all_deposits + (?)', (amount,))
		cursor.execute('UPDATE users SET all_deposit = all_deposit + (?) WHERE user_id = (?)', (amount, call.from_user.id))
		cursor.execute('UPDATE users SET balance = balance + (?) WHERE user_id = (?)', (amount, call.from_user.id))
		conn.commit()
		conn.close()
		await menu(call.from_user.id)
		await call.message.answer(f'✅ <b>Начислено</b> <i>{amount}</i> <b>RUB на баланс</b>')
		await bot.send_message(ADMIN, f'<b>✅ Новое пополнение!:\n\n<i>Пользователь: @{call.message.chat.username}\nСумма {amount} RUB \nМетод: QIWI/CARD\nID платежа: <code>{pid}</code></i></b>')
	else:
		await call.answer(f'⛔️ Оплата не замечена',show_alert=False)


async def YOO_PAY(summa, user_id):
	try:
		#conn = sqlite3.connect('db.db', check_same_thread=False)
		#cursor = conn.cursor()
		#cursor.execute('SELECT YOO_KEY FROM settings')
		#YOO_KEY = cursor.fetchone()[0]
		#conn.close()
		await bot.send_invoice(user_id, "Пополнение баланса", "Пополнение баланса в боте PROXY_BOT", "add_balance", config.YOOMONEY_KEY, "RUB", start_parameter="PROXY_BOT", prices=[{"label": "Руб", "amount": int(summa) * 100}])
	except Exception as e:
		await bot.send_message(chat_id=ADMIN, text=f'Ошибка пополнения ЮKassa:\n{e}')
		await menu(user_id)
		await bot.send_message(chat_id=user_id,
							   text='<b><i>Депозит через ЮKassa временно недоступно...\nМы уже занимаемся этим вопросом</i></b>')



async def Lava(summa, user_id):
    oplata = AioLava(SECRET_KEY, PROJECT_ID)
    try:
        invoice = await oplata.create_invoice(summa)
        print(invoice.invoice_id)
        invoice_id = invoice.invoice_id
        print('инвойс создан, функция лава')
        keyboard = types.InlineKeyboardMarkup(row_width = 2)
        buttons = [
        types.InlineKeyboardButton(text = "💳 Оплатить", url = invoice.url),
        types.InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f'lava_{invoice.invoice_id}_{summa}'),
        ]
        keyboard.add(*buttons)
        await bot.send_message(chat_id = user_id, text = f'<b><i>💴 Сумма к оплате: {summa} RUB</i></b>', reply_markup = keyboard)
    except Exception as e:
        print(e)
        await bot.send_message(chat_id = ADMIN, text = f'Ошибка пополнения LAVA:\n{e}')
        await menu(user_id)
        await bot.send_message(chat_id = user_id, text ='<b>Депозит через LAVA временно недоступно...\nМы уже занимаемся этим вопросом</b>')
        


