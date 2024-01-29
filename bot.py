import requests
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
import logging
import sqlite3
from pycbrf.toolbox import ExchangeRates
from telethon import TelegramClient, events
from LavaBusiness import AioLava

from functions import *
from config import *
from keyboards import *
from rules import get_rules
from country import COUNTRY



# asyncio.run(getRates())

# logging.basicConfig(level=logging.INFO)

class SET_PROXY_PARAMS(StatesGroup):
    GET_PROXY_COUNT = State()


class QIWI_DEPOSIT(StatesGroup):
    GET_AMOUNT = State()


class YOO_DEPOSIT(StatesGroup):
    GET_AMOUNT = State()


class RASSIKA(StatesGroup):
    only_text = State()
    text_and_photo = State()


class NACENKA(StatesGroup):
    go = State()


class BALANCE(StatesGroup):
    user = State()
    money = State()

class AioLava_DEPOSIT(StatesGroup):
    GET_AMOUNT = State()
    


bot = Bot(token=BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())


async def anti_flood(*args, **kwargs):
    m = args[0]
    try:
        await m.answer("📛 Не флуди!", show_alert=True)
    except:
        await m.answer("📛 Не флуди!")


# async def set_bot_commands(dispatcher: Dispatcher):

# bot_commands = [
# types.BotCommand(command="/start", description="старт бота")
# ]

# bot.set_my_commands(bot_commands)


# старт
@dp.message_handler(commands=['start'])
@dp.throttled(anti_flood, rate=0)
async def start(message):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    in_base = await CHECK_IN_BASE(message.from_user.id)
    if in_base != None:
        await menu(message.from_user.id)
    else:
        cursor.execute('INSERT INTO users (user_id) VALUES (?)', (message.from_user.id,))
        conn.commit()
        await menu(message.from_user.id)
        await message.answer(await get_rules(USERNAME), reply_markup=await close_message_keyboard())


# Меню прокси
@dp.message_handler(text='📲 Купить')
@dp.throttled(anti_flood, rate=0)
async def proxy_main(message):
    # await bot.send_photo(chat_id=message.from_user.id, photo=IMAGE, caption=
    await bot.send_photo(chat_id=message.from_user.id, photo=PROXY_IMAGE, caption='<b>💬 Выберите действие:</b>',
                         reply_markup=await proxy_main_keyboard())


@dp.message_handler(text='🖥 Профиль')
@dp.throttled(anti_flood, rate=0)
async def profile_main(message):
    await profile(message)


@dp.message_handler(text='ℹ️ Информация')
@dp.throttled(anti_flood, rate=0)
async def info_main(message):
    await info(message)


@dp.message_handler(text='Админка')
@dp.throttled(anti_flood, rate=0)
async def adminka_main(message):
    admin = await GET_ADMIN_STATUS(message.from_user.id)
    if admin == 1:
        await adminka(message)


@dp.message_handler(text='Сделать рассылку')
async def get_rassilka(message):
    admin = await GET_ADMIN_STATUS(message.from_user.id)
    if admin == 1:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(*[
            types.KeyboardButton(text='С фото'),
            types.KeyboardButton(text='Текст')
        ])
        keyboard.add(types.KeyboardButton('Меню'))
        await message.answer('Выберите тип рассылки:', reply_markup=keyboard)


@dp.message_handler(text='С фото')
async def text_to_photo_rassilka(message):
    admin = await GET_ADMIN_STATUS(message.from_user.id)
    if admin == 1:
        await RASSIKA.text_and_photo.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            types.KeyboardButton('Меню')
        )
        await message.answer('Введите текст:', reply_markup=keyboard)


@dp.message_handler(state=RASSIKA.text_and_photo)
async def photo_to_photo_rassilka(message, state):
    if message.text != 'Меню':
        await state.update_data(text=message.text)
        await message.answer('Отправьте фото:')
    else:
        await state.finish()
        await menu(message.from_user.id)


# await state.reset_state(with_data=False)

@dp.message_handler(content_types=['photo'], state=RASSIKA.text_and_photo)
async def get_photo_rassilka(message, state=RASSIKA.text_and_photo):
    await start_photo_rassilka(message, state)


@dp.message_handler(text='Текст')
async def text_to_photo_rassilka(message):
    admin = await GET_ADMIN_STATUS(message.from_user.id)
    if admin == 1:
        await RASSIKA.only_text.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            types.KeyboardButton('Меню')
        )
        await message.answer('Введите текст:', reply_markup=keyboard)


@dp.message_handler(state=RASSIKA.only_text)
async def get_only_text_rassilka(message, state):
    if message.text != 'Меню':
        await start_text_rassilka(message, state)
    else:
        await state.finish()
        await menu(message.from_user.id)


@dp.message_handler(text='Меню', state="*")
@dp.throttled(anti_flood, rate=0)
async def main(message, state):
    await state.finish()
    await menu(message.from_user.id)


@dp.message_handler(text='Изменить наценку')
async def reset_nachenka(message):
    admin = await GET_ADMIN_STATUS(message.from_user.id)
    if admin == 1:
        await NACENKA.go.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            types.KeyboardButton('Меню')
        )
        await message.answer('Введите целое число:', reply_markup=keyboard)


@dp.message_handler(state=NACENKA.go)
async def set_nacenka(message, state):
    if message.text.isdigit():
        conn = sqlite3.connect('db.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE settings SET nacenka = (?)', (message.text,))
        conn.commit()
        conn.close()
        await message.answer(f'Наценка изменена на {message.text}₽', reply_markup=await admin_keyboard())
    else:
        await menu(message.from_user.id)
    await state.finish()


@dp.message_handler(text='Выдать баланс')
async def set_user_id_BALANCE(message):
    admin = await GET_ADMIN_STATUS(message.from_user.id)
    if admin == 1:
        await BALANCE.user.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            types.KeyboardButton('Меню')
        )
        await message.answer('Введите id пользователя:', reply_markup=keyboard)


@dp.message_handler(state=BALANCE.user)
async def set_money_BALANCE(message, state):
    if message.text.isdigit():
        conn = sqlite3.connect('db.db', check_same_thread=False)
        cursor = conn.cursor()
        info = cursor.execute('SELECT * FROM users WHERE user_id = (?)', (int(message.text),)).fetchone()
        if info != None:
            await BALANCE.money.set()
            await state.update_data(user_id=message.text)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                types.KeyboardButton('Меню')
            )
            await message.answer('Введите сумму целым числом:', reply_markup=keyboard)
        else:
            await message.answer('Такого пользователя не существует', reply_markup=await admin_keyboard())
            await state.finish()

    else:
        await menu(message.from_user.id)
        await state.finish()


@dp.message_handler(state=BALANCE.money)
async def send_balance(message, state):
    try:
        if message.text.isdigit():
            user = await state.get_data()
            user_id = user['user_id']
            conn = sqlite3.connect('db.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET balance = balance + (?) WHERE user_id = (?)',
                           (int(message.text), int(user_id)))
            conn.commit()
            conn.close()
            await bot.send_message(chat_id=user_id, text=f'Ваш баланс пополнен на {message.text}₽',
                                   reply_markup=await menu_keyboard(int(user_id)))
            await message.answer(f'Пользователь {user_id} получил {message.text}₽', reply_markup=await admin_keyboard())
        else:
            await menu(message.from_user.id)
    except Exception as e:
        raise e
    finally:
        await state.finish()


@dp.callback_query_handler(text='get_rules')
async def send_rules(call):
    await call.message.answer(await get_rules(USERNAME), reply_markup=await close_message_keyboard())


@dp.callback_query_handler(text='delete_message')
async def delete_message(call):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)


# Выбор типа прокси
@dp.callback_query_handler(text='get_proxy_type')
@dp.throttled(anti_flood, rate=0)
async def get_proxy_type(call):
    # await bot.delete_message(chat_id= call.from_user.id, message_id= call.message.message_id)
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption='<b>🔍 Выберите тип прокси:</b>',
                                   reply_markup=await get_proxy_type_keyboard())


@dp.callback_query_handler(text_contains='set_type')
@dp.throttled(anti_flood, rate=0)
async def set_proxy_type(call, state=SET_PROXY_PARAMS):
    # await bot.delete_message(chat_id = call.from_user.id, message_id= call.message.message_id)
    infolist = call.data.split('|')
    ttype = infolist[1]
    ipv = infolist[2]
    await state.update_data(type=ttype, ipv=ipv)
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption='<b>🌎 Выберите страну:</b>', reply_markup=await get_country_keyboard(0))


@dp.callback_query_handler(text_contains='next_country')
@dp.throttled(anti_flood, rate=0)
async def next_country(call):
    i = call.data[13:]
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption='<b>🌎 Выберите страну:</b>', reply_markup=await get_country_keyboard(i))


@dp.callback_query_handler(text_contains='set_country_')
@dp.throttled(anti_flood, rate=0)
async def set_proxy_country(call, state=SET_PROXY_PARAMS):
    country = call.data.split('|')
    country_code = country[1]
    country_name = country[2]
    await state.update_data(country_code=country_code, country_name=country_name)
    # await bot.delete_message(chat_id = call.from_user.id, message_id= call.message.message_id)
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption='<b>🏙 Выберите город:</b>',
                                   reply_markup=await get_city_keyboard(country_code))


@dp.callback_query_handler(text_contains='set_city_')
@dp.throttled(anti_flood, rate=0)
async def set_proxy_city(call, state=SET_PROXY_PARAMS):
    city = call.data.split('|')
    city_code = city[1]
    city_name = city[2]
    await state.update_data(city_code=city_code, city_name=city_name)
    # await bot.delete_message(chat_id = call.from_user.id, message_id= call.message.message_id)
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption='<b>🕔 Выберите период (ДНИ)</b>', reply_markup=await get_period_keyboard())


@dp.callback_query_handler(text_contains='set_period_')
@dp.throttled(anti_flood, rate=0)
async def set_proxy_period(call, state=SET_PROXY_PARAMS):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    msg = await call.message.answer('⏳')
    period = call.data[11:]
    await state.update_data(period=period)
    infolist = await state.get_data()
    ipv = infolist['ipv']
    types = infolist['type']
    country = infolist['country_code']
    all_count = requests.get(
        f'https://panel.proxyline.net/api/ips-count/?api_key={PROXY_KEY}&ip_version={ipv}&type={types}&country={country}').json()
    print(all_count)
    all_count = all_count.get('count')
    if all_count != 0:
        await state.update_data(count=all_count)
        await bot.delete_message(chat_id=call.from_user.id, message_id=msg.message_id)
        await bot.send_photo(chat_id=call.from_user.id, photo=PROXY_IMAGE,
                             caption=f'<b>✏️ Введите количество прокси, которое вы хотите приобрести:</b>\n<i>🔎 Доступно: {all_count} шт</i>')
        await SET_PROXY_PARAMS.GET_PROXY_COUNT.set()
    else:
        await call.message.answer('😢 Нет доступных прокси', reply_markup=menu_keyboard(call.from_user.id))


@dp.message_handler(state=SET_PROXY_PARAMS.GET_PROXY_COUNT)
@dp.throttled(anti_flood, rate=0)
async def set_proxy_count(message, state):
    try:
        if message.text.isdigit():
            infolist = await state.get_data()
            # print(infolist)
            count_proxy = infolist['count']
            if int(message.text) <= int(count_proxy):
                # print(count_proxy)
                # print(infolist)
                await state.update_data(count=message.text)
                # requests.get(f'https://panel.proxyline.net/api/ips/?api_key={PROXY_API}&ip_version=4&type=dedicated&country=ru')
                params = {
                    'ip_version': infolist['ipv'],
                    'type': infolist['type'],
                    'country': infolist['country_code'],
                    'city': infolist['city_code']
                }
                info_ip = requests.get(f'https://panel.proxyline.net/api/ips/?api_key={PROXY_KEY}',
                                       params=params).json()
                print(info_ip)
                ip_list = []
                i = 0
                for ip in info_ip:
                    print(ip)
                    if i < int(message.text):
                        ip_list.append(ip.get('id'))
                        i += 1
                params = {
                    'type': infolist['type'],
                    'ip_version': infolist['ipv'],
                    'country': infolist['country_code'],
                    'quantity': message.text,
                    'period': infolist['period'],
                    'city': infolist['city_code'],
                    'ip_list': ip_list
                }
                await state.update_data(params=params)
                info = requests.post(f'https://panel.proxyline.net/api/new-order-amount/?api_key={PROXY_KEY}',
                                     data=params).json()
                # print(info)
                if 'non_field_errors' not in info:
                    keyboard = types.InlineKeyboardMarkup(row_width=2)
                    price = await getRates(info.get('amount')) + await DB_GET_NACENKA()
                    keyboard.add(
                        types.InlineKeyboardButton(text=f'Оплатить {price} ₽', callback_data=f'buy_proxy|{price}'))
                    await bot.send_photo(chat_id=message.from_user.id, photo=PROXY_IMAGE, caption='''

<b><i>❗️ВНИМАНИЕ!!! ПРОКСИ ПОДХОДЯТ ТОЛЬКО ДЛЯ БЕЛЫХ ЦЕЛЕЙ</i></b>
<b><i>⚙️Параметры прокси:</i></b>

🥷 <b>Тип прокси:</b> <i>{0}</i>
🔐 <b>Версия IP:</b> <i>{1}</i>
🌎 <b>Страна:</b> <i>{2}</i>
🏙 <b>Город:</b> <i>{3}</i>
🐉 <b>Количество:</b> <i>{4} шт</i>
🕔 <b>Период:</b> <i>{5} дней</i>


						'''.format(infolist['type'], infolist['ipv'], infolist['country_name'], infolist['city_name'],
                                   len(ip_list), infolist['period']), reply_markup=keyboard)
                    await state.reset_state(with_data=False)
                else:
                    await menu(message.from_user.id)
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='<b><i>😥 В данный момент нет свободный серверов в этом городе\n⏳ Попробуйте позже</i></b>')
                    await state.finish()
            else:
                await bot.send_message(chat_id=message.from_user.id,
                                       text='<b>😥 Вы превысили кол-во доступных прокси\n✏️ Введите количество еще раз или нажмите "Отмена" </b>')
            # await set_proxy_period(message, state=SET_COUNT_PROXY, how=1)
        else:
            await menu(message.from_user.id)
            await state.finish()
    except Exception as e:
        print(e)
    # raise e


@dp.callback_query_handler(text_contains='buy_proxy')
@dp.throttled(anti_flood, rate=0)
async def buy_proxy(call, state=SET_PROXY_PARAMS.GET_PROXY_COUNT):
    infolist = call.data.split('|')
    price = infolist[1]
    # print(price)
    try:
        if float(price) <= await DB_GET_BALANCE(call.from_user.id):
            infolist = await state.get_data()
            # print(infolist)
            params = infolist['params']
            info = requests.post(f'https://panel.proxyline.net/api/new-order/?api_key={PROXY_KEY}', data=params).json()
            if 'non_field_errors' in info:
                e_text = info.get('non_field_errors')
                if 'Not enough money on balance' in e_text:
                    await bot.send_message(ADMIN,
                                           text='⚠️ <b>Не хватает баланса на сайте для покупки прокси\n\n⚠️Пополните баланс</b>')
                await call.answer('😥 Попробуйте позже')
            else:
                await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
                conn = sqlite3.connect('db.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET all_buy = all_buy + 1 WHERE user_id = (?)', (call.from_user.id,))
                cursor.execute('UPDATE users SET balance = balance - (?) WHERE user_id = (?)',
                               (price, call.from_user.id))
                conn.commit()
                await menu(call.from_user.id)
                for i in info:
                    ids = i.get('id')
                    ip = i.get('ip')
                    http_port = i.get('port_http')
                    socks5_port = i.get('port_socks5')
                    user = i.get('user')
                    username = i.get('username')
                    password = i.get('password')
                    date_end = i.get('date_end')
                    cursor.execute(
                        'INSERT INTO proxy_list (user_id, ids, ip, http_port, socks5_port, username, password, date_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (call.from_user.id, ids, ip, http_port, socks5_port, username, password, date_end[:10]))
                    conn.commit()
                    proxy_info = f'''
<b>ID заказа:</b> <code>{ids}</code>

<b>IP:</b> <code>{ip}</code>
<b>HTTP порт:</b> <code>{http_port}</code>
<b>SOCKS5 порт:</b> <code>{socks5_port}</code>
<b>Имя пользователя:</b> <code>{username}</code>
<b>Пароль:</b> <code>{password}</code>

<b>Дата окончания:</b> {date_end[:10]}
					'''
                    await call.message.answer(proxy_info)
                    await bot.send_message(ADMIN, text=f'<b>💸 Куплены прокси:</b>\n\n{proxy_info}')
                conn.close()
        else:
            await call.answer('😥 Не хватает баланса')
    except Exception as e:
        await call.answer('😥 Попробуйте позже')
        raise e


@dp.callback_query_handler(text='my_proxy')
@dp.throttled(anti_flood, rate=0)
async def get_my_proxy(call):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    row = cursor.execute('SELECT ids, ip, date_end FROM proxy_list WHERE user_id = (?)',
                         (call.from_user.id,)).fetchall()
    btn = []
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    if row != []:
        for i in row:
            date_end = datetime.datetime.strptime(i[2], '%Y-%m-%d')
            ids = i[0]
            if date_end < datetime.datetime.now():
                cursor.execute('DELETE FROM proxy_list WHERE ids = (?)', (ids,))
                conn.commit()
            else:
                btn.append(types.InlineKeyboardButton(text=i[1], callback_data=f'proxy_info_{ids}'))
    if btn != []:
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        keyboard.add(*btn)
        # keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data='proxy_menu'))
        await call.message.answer(
            '<b>📁 Список активных прокси:</b>\n<i>🕔 По истечению срока они удалятся из списка</i>',
            reply_markup=keyboard)
    else:
        await call.answer('👣 Нет активных прокси')
    conn.close()


@dp.callback_query_handler(text_contains='proxy_info_')
@dp.throttled(anti_flood, rate=0)
async def get_my_proxy(call):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    ids = call.data[11:]
    row = cursor.execute('SELECT * FROM proxy_list WHERE ids = (?)', (int(ids),)).fetchone()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='my_proxy'))
    await call.message.answer(
        '''
<b>ID заказа:</b> <code>{0}</code>

<b>IP:</b> <code>{1}</code>
<b>HTTP порт:</b> <code>{2}</code>
<b>SOCKS5 порт:</b> <code>{3}</code>
<b>Имя пользователя:</b> <code>{4}</code>
<b>Пароль:</b> <code>{5}</code>

<b>Дата окончания:</b> {6}

		'''.format(row[1], row[2], row[3], row[4], row[5], row[6], row[7]), reply_markup=keyboard
    )
    conn.close()


@dp.callback_query_handler(text='deposit')
@dp.throttled(anti_flood, rate=0)
async def get_deposit_main(call):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await bot.send_photo(chat_id=call.from_user.id, photo=MENU_IMAGE, caption='<b>🌐 Выберите способ оплаты:</b>',
                         reply_markup=await deposit_keyboard())


@dp.message_handler(text='💳 QIWI/CARD')
@dp.throttled(anti_flood, rate=0)
async def get_summa_qiwi(message):
    await QIWI_DEPOSIT.GET_AMOUNT.set()
    await message.answer('<b><i>✏️ Введите сумму пополнения:</i></b>')


@dp.message_handler(text='💜 ЮKassa')
@dp.throttled(anti_flood, rate=0)
async def get_summa_yoo(message):
    await YOO_DEPOSIT.GET_AMOUNT.set()
    await message.answer('<b><i>✏️ Введите сумму пополнения:</i></b>')


@dp.message_handler(text='💜 Lava')
@dp.throttled(anti_flood, rate=0)
async def get_summa_AioLava(message):
    await AioLava_DEPOSIT.GET_AMOUNT.set()
    await message.answer('<b><i>✏️ Введите сумму пополнения:</i></b>')
    

@dp.message_handler(state=QIWI_DEPOSIT.GET_AMOUNT)
@dp.throttled(anti_flood, rate=0)
async def generate_pay_link(message, state):
    if message.text.isdigit() and int(message.text) < 1000000:
        await QIWI_PAY(message.text, message.from_user.id)
    else:
        await message.answer('<b><i>⚠️ Введите целое число!</i></b>')


@dp.message_handler(state=YOO_DEPOSIT.GET_AMOUNT)
@dp.throttled(anti_flood, rate=0)
async def generate_pay_link(message, state):
    if message.text.isdigit() and int(message.text) < 1000000 and int(message.text) >= 60:
        await YOO_PAY(message.text, message.from_user.id)
        await state.update_data(amount=message.text)
        await state.set_state("check")
    else:
        await message.answer('<b><i>⚠️ Введите целое число! Минимальная сумма 60 RUB</i></b>')
        
        
@dp.message_handler(state=AioLava_DEPOSIT.GET_AMOUNT)
@dp.throttled(anti_flood, rate=0)
async def generate_pay_link(message: types.Message, state: FSMContext):
    if message.text.isdigit() and int(message.text) < 1000000:
        await Lava(message.text, message.from_user.id)
    else:
        await message.answer('<b><i>⚠️ Введите целое число!</i></b>')
    
    await state.reset_state()

@dp.callback_query_handler(text_startswith='lava')
async def lavacheck_func(call: types.CallbackQuery):
    print('функция проверки лава')
    oplata = AioLava(SECRET_KEY, PROJECT_ID)
    invoice_id = call.data.split('_')[1]
    print(invoice_id)
    summa = call.data.split('_')[2]
    status = await oplata.invoice_status(invoice_id)
    print('Функция оплаты лавы 2')
    print(status)
    if status == 'success':
        await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)
        

        conn = sqlite3.connect('db.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE settings SET all_deposits = all_deposits + (?)', (summa,))
        cursor.execute('UPDATE users SET all_deposit = all_deposit + (?) WHERE user_id = (?)', (summa, call.from_user.id))
        cursor.execute('UPDATE users SET balance = balance + (?) WHERE user_id = (?)', (summa, call.from_user.id))
        conn.commit()
        await menu(call.from_user.id)
        
        await call.message.answer(f'✅ <b>Начислено</b> <i>{summa}</i> <b>RUB на баланс</b>')
        await bot.send_message(ADMIN, f'<b>✅ Новое пополнение!:\n\n<i>Пользователь: @{call.message.chat.username}\nСумма {summa} RUB \nМетод: QIWI/CARD\nID платежа: <code>{invoice_id}</code></i></b>')
    elif status == 'expired':
        await call.answer(f'⚠️ Счет просрочен',show_alert=False)
    elif status == 'created':
        await call.answer(f'Оплата только создана.')
    else:
        await call.answer(f'⛔️ Оплата не замечена',show_alert=False)


@dp.pre_checkout_query_handler(state="check")
async def check(call: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(call.id, ok=True)


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT, state="*")
async def process_pay_success(message: types.Message, state):
    if message.successful_payment.invoice_payload == "add_balance":
        datalist = await state.get_data()
        print(datalist)
        amount = int(datalist['amount'])

        conn = sqlite3.connect('db.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE settings SET all_deposits = all_deposits + (?)', (amount,))
        cursor.execute('UPDATE users SET all_deposit = all_deposit + (?) WHERE user_id = (?)',
                       (amount, message.from_user.id))
        cursor.execute('UPDATE users SET balance = balance + (?) WHERE user_id = (?)', (amount, message.from_user.id))
        conn.commit()
        conn.close()
        await menu(message.from_user.id)
        await bot.send_message(message.from_user.id, f'✅ <b>Начислено</b> <i>{amount}</i> <b>RUB на баланс</b>')
        await state.finish()
        await bot.send_message(ADMIN,
                               f'<b>✅ Новое пополнение!:\n\n<i>Пользователь: @{message.chat.username}\nСумма {amount} RUB \nМетод: ЮKassa</i></b>')




@dp.callback_query_handler(text_contains='CheckQiwi_')
@dp.throttled(anti_flood, rate=2)
async def check_qiwi_func(call):
    await check_qiwi(call)


@dp.message_handler(text="Включить ЮKassa")
async def en_yoo(message):
    if message.from_user.id != ADMIN:
        return
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET yoo_active = 1')
    conn.commit()
    conn.close()
    await message.answer("✅ ЮKassa включена!")


@dp.message_handler(text="Выключить ЮKassa")
async def off_yoo(message):
    if message.from_user.id != ADMIN:
        return
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET yoo_active = 0')
    conn.commit()
    conn.close()
    await message.answer("✅ ЮKassa выключена!")


@dp.message_handler(text="Включить QIWI")
async def en_qiwi(message):
    if message.from_user.id != ADMIN:
        return
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET qiwi_active = 1')
    conn.commit()
    conn.close()
    await message.answer("✅ QIWI включена!")


@dp.message_handler(text="Выключить QIWI")
async def off_qiwi(message):
    if message.from_user.id != ADMIN:
        return
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET qiwi_active = 0')
    conn.commit()
    conn.close()
    await message.answer("✅ QIWI выключена!")


@dp.message_handler(text="Включить Lava")
async def en_AioLava(message):
    if message.from_user.id != ADMIN:
        return
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET yoo_active = 1')
    conn.commit()
    conn.close()
    await message.answer("✅ Lava включена!")


@dp.message_handler(text="Выключить Lava")
async def off_AioLava(message):
    if message.from_user.id != ADMIN:
        return
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET yoo_active = 0')
    conn.commit()
    conn.close()
    await message.answer("✅ Lava выключена!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
