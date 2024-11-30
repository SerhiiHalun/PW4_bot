import os
import logging
import asyncio
import sqlite3

import requests
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

import stripe
from db_utils import add_user, get_user_balance, update_user_balance, complete_registration, is_user_registered, init_db, get_quadcopters

logging.basicConfig(level=logging.INFO)

STRIPE_API_KEY = 'sk_test_51QKny4E16NJAzYbG69Ta7BGDZMBMpvFfAQbHTzd127L3QkrXqoAa3SITQYCqEfrLeUTfTW8qkMrRSUrOKscuwwOK00gunUEyG3'
BOT_TOKEN = '7536510926:AAGBdMUwCDZ0U-lspNNwY_iXuw_18-xTv1U'
stripe.api_key = STRIPE_API_KEY

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class TopUpStates(StatesGroup):
    waiting_for_amount = State()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()

class QuadcopterSelectionStates(StatesGroup):
    waiting_for_budget = State()
    waiting_for_flight_time = State()
    waiting_for_range = State()
    waiting_for_camera_quality = State()
    waiting_for_portability = State()

class CurrencySettingsStates(StatesGroup):
    waiting_for_currency_choice = State()

user_currency_preferences = {} 

def get_currency_conversion_rate(target_currency):
    try:
        response = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json")
        if response.status_code == 200:
            rates = response.json()
            for rate in rates:
                if rate['cc'].lower() == target_currency.lower():
                    return rate['rate']
        return None
    except Exception as e:
        logging.error(f"Error fetching currency rates: {e}")
        return None

def convert_currency(amount, target_currency):
    if target_currency.lower() == 'uah':
        return amount
    rate = get_currency_conversion_rate(target_currency)
    if rate:
        return round(amount / rate, 2)
    return None

def convert_price_for_quadcopters(quadcopters, target_currency):
    if target_currency.lower() == 'uah':
        return quadcopters

    rate = get_currency_conversion_rate(target_currency)
    if rate:
        converted_quadcopters = []
        for quad in quadcopters:
            converted_price = round(quad[2] / rate, 2)
            converted_quadcopters.append((quad[0], quad[1], converted_price, *quad[3:]))
        return converted_quadcopters
    return quadcopters

def get_main_keyboard(is_registered=False):
    if is_registered:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='/balance'),
                    KeyboardButton(text='/topup'),
                    KeyboardButton(text='/find_quadcopter'),
                    KeyboardButton(text='/currency_settings')
                ]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='/register')
                ]
            ],
            resize_keyboard=True
        )

@dp.message(Command('currency_settings'))
async def cmd_currency_settings(message: types.Message, state: FSMContext):
    await message.answer("Будь ласка, оберіть бажану валюту: UAH, USD, EUR")
    await state.set_state(CurrencySettingsStates.waiting_for_currency_choice)

@dp.message(CurrencySettingsStates.waiting_for_currency_choice)
async def process_currency_choice(message: types.Message, state: FSMContext):
    currency = message.text.strip().upper()
    if currency not in ['UAH', 'USD', 'EUR']:
        await message.answer("Invalid currency. Please choose from UAH, USD, EUR.")
        return

    user_currency_preferences[message.from_user.id] = currency
    await message.answer(f"Your preferred currency has been set to {currency}.")
    await state.clear()

@dp.message(Command('balance'))
async def cmd_balance(message: types.Message):
    if not is_user_registered(message.from_user.id):
        await message.answer("Спочатку потрібно зареєструватися за допомогою /register.")
        return

    balance = get_user_balance(message.from_user.id)
    user_currency = user_currency_preferences.get(message.from_user.id, 'UAH')
    if user_currency != 'UAH':
        converted_balance = convert_currency(balance, user_currency)
        if converted_balance is not None:
            await message.answer(f"Ваш поточний баланс становить: {converted_balance} {user_currency}.")
        else:
            await message.answer("Не вдається конвертувати баланс. Відображається баланс у гривнях.")
            await message.answer(f"Ваш поточний баланс становить: {balance} UAH.")
    else:
        await message.answer(f"Ваш поточний баланс становить: {balance} UAH.")


@dp.message(Command('topup'))
async def cmd_topup(message: types.Message, state: FSMContext):
    if not is_user_registered(message.from_user.id):
        await message.answer("YСпочатку потрібно зареєструватися за допомогою /register.")
        return

    user_currency = user_currency_preferences.get(message.from_user.id, 'UAH')
    await message.answer(f"Введіть суму, яку хочете поповнити (in {user_currency}):")
    await state.set_state(TopUpStates.waiting_for_amount)


@dp.message(TopUpStates.waiting_for_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("Сума повинна бути більшою за 0.")
            return

        user_currency = user_currency_preferences.get(message.from_user.id, 'UAH')
        if user_currency != 'UAH':
            rate = get_currency_conversion_rate(user_currency)
            if rate:
                amount = round(amount * rate, 2)
            else:
                await message.answer("Не вдалося конвертувати суму в гривні. Будь ласка, спробуйте пізніше.")
                return

        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency='uah',
            payment_method_types=['card']
        )

        update_user_balance(message.from_user.id, amount)
        await message.answer(f"Посилання для оплати: {payment_intent.client_secret}\n Ваш баланс поповнився на {amount} UAH.")
        await state.clear()
    except ValueError:
        await message.answer("Будь ласка, введіть правильну суму.")
    except Exception as e:
        logging.error(f"Помилка обробки суми поповнення: {e}")
        await message.answer("Під час обробки вашого запиту сталася помилка.")

def get_main_keyboard(is_registered=False):
    if is_registered:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='/balance'),
                    KeyboardButton(text='/topup'),
                    KeyboardButton(text='/find_quadcopter')
                ]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='/register')
                ]
            ],
            resize_keyboard=True
        )

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    is_registered = is_user_registered(message.from_user.id)
    await message.answer(
        "Ласкаво просимо! Використовуйте /balance для перевірки балансу, /topup для поповнення рахунку. Спочатку зареєструйтесь за допомогою /register.",
        reply_markup=get_main_keyboard(is_registered)
    )

@dp.message(Command('register'))
async def cmd_register(message: types.Message, state: FSMContext):
    if is_user_registered(message.from_user.id):
        await message.answer("Ви вже зареєстровані.")
        return

    await message.answer("Реєстрація: Будь ласка, введіть ваше повне ім'я:")
    await state.set_state(RegistrationStates.waiting_for_name)

@dp.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer("Будь ласка, введіть своє повне ім'я (ім'я та прізвище).")
        return

    await state.update_data(full_name=full_name)
    await message.answer("Enter your email address:")
    await state.set_state(RegistrationStates.waiting_for_email)

@dp.message(RegistrationStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if '@' not in email:
        await message.answer("Будь ласка, введіть дійсну адресу електронної пошти.")
        return

    await state.update_data(email=email)
    await message.answer("Введіть свій номер телефону:")
    await state.set_state(RegistrationStates.waiting_for_phone)

@dp.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.replace('+', '').isdigit():
        await message.answer("Будь ласка, введіть дійсний номер телефону.")
        return

    user_data = await state.get_data()
    complete_registration(
        message.from_user.id,
        user_data['full_name'],
        user_data['email'],
        phone
    )

    await message.answer(
        "Реєстрація завершена! Тепер ви можете використовувати всі функції бота.",
        reply_markup=get_main_keyboard(True)
    )
    await state.clear()

@dp.message(Command('balance'))
async def cmd_balance(message: types.Message):
    if not is_user_registered(message.from_user.id):
        await message.answer("Спочатку потрібно зареєструватися за допомогою /register.")
        return

    balance = get_user_balance(message.from_user.id)
    await message.answer(f"Ваш поточний баланс становить {balance} UAH.")

@dp.message(Command('topup'))
async def cmd_topup(message: types.Message, state: FSMContext):
    if not is_user_registered(message.from_user.id):
        await message.answer("Спочатку потрібно зареєструватися за допомогою /register.")
        return

    await message.answer("Введіть суму, яку ви хочете поповнити:")
    await state.set_state(TopUpStates.waiting_for_amount)

@dp.message(TopUpStates.waiting_for_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("Сума повинна бути більшою за 0.")
            return

        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency='uah',
            payment_method_types=['card']
        )

        update_user_balance(message.from_user.id, amount)
        await message.answer(f"Payment link: {payment_intent.client_secret}\n Ваш баланс поповнився на {amount} UAH.")
        await state.clear()
    except ValueError:
        await message.answer("Будь ласка, введіть правильну суму.")
    except Exception as e:
        logging.error(f"Помилка обробки суми поповнення: {e}")
        await message.answer("An error occurred while processing your request.")


@dp.message(Command('find_quadcopter'))
async def cmd_find_quadcopter(message: types.Message, state: FSMContext):
    user_currency = user_currency_preferences.get(message.from_user.id, 'UAH')
    await message.answer(f"Будь ласка, введіть свій бюджет у поле {user_currency}:")
    await state.set_state(QuadcopterSelectionStates.waiting_for_budget)

@dp.message(QuadcopterSelectionStates.waiting_for_budget)
async def process_budget(message: types.Message, state: FSMContext):
    try:
        budget = float(message.text)
        if budget <= 0:
            await message.answer("Бюджет повинен бути більше 0. Будь ласка, введіть ще раз.")
            return

        user_currency = user_currency_preferences.get(message.from_user.id, 'UAH')
        if user_currency != 'UAH':
            rate = get_currency_conversion_rate(user_currency)
            if rate:
                budget = round(budget * rate, 2)
            else:
                await message.answer("Не вдалося конвертувати бюджет у гривні. Будь ласка, спробуйте пізніше.")
                return

        await state.update_data(budget=budget)
        await message.answer("Який максимальний час польоту вам потрібен (у хвилинах)?")
        await state.set_state(QuadcopterSelectionStates.waiting_for_flight_time)
    except ValueError:
        await message.answer("Будь ласка, введіть правильний номер.")

@dp.message(QuadcopterSelectionStates.waiting_for_flight_time)
async def process_flight_time(message: types.Message, state: FSMContext):
    try:
        flight_time = int(message.text)
        if flight_time <= 0:
            await message.answer("Час польоту має бути більше 0. Введіть ще раз.")
            return

        await state.update_data(flight_time=flight_time)
        await message.answer("Який максимальний радіус дії вам потрібен (у метрах)?")
        await state.set_state(QuadcopterSelectionStates.waiting_for_range)
    except ValueError:
        await message.answer("Please enter a valid number.")

@dp.message(QuadcopterSelectionStates.waiting_for_range)
async def process_range(message: types.Message, state: FSMContext):
    try:
        range_ = int(message.text)
        if range_ <= 0:
            await message.answer("Range must be greater than 0. Please enter again.")
            return

        await state.update_data(range=range_)
        await message.answer("Яка якість камери вам потрібна (наприклад, HD, 4K)?")
        await state.set_state(QuadcopterSelectionStates.waiting_for_camera_quality)
    except ValueError:
        await message.answer("Please enter a valid number.")

@dp.message(QuadcopterSelectionStates.waiting_for_camera_quality)
async def process_camera_quality(message: types.Message, state: FSMContext):
    camera_quality = message.text.strip()
    await state.update_data(camera_quality=camera_quality)
    await message.answer("Наскільки важливою є переносимість (e.g., high, medium, low)?")
    await state.set_state(QuadcopterSelectionStates.waiting_for_portability)

@dp.message(QuadcopterSelectionStates.waiting_for_portability)
async def process_portability(message: types.Message, state: FSMContext):
    portability = message.text.strip().lower()
    user_data = await state.get_data()
    budget = user_data['budget']
    flight_time = user_data['flight_time']
    range_ = user_data['range']
    camera_quality = user_data['camera_quality']

    quadcopters = get_quadcopters(budget, flight_time, range_)
    user_currency = user_currency_preferences.get(message.from_user.id, 'UAH')
    quadcopters = convert_price_for_quadcopters(quadcopters, user_currency)

    if not quadcopters:
        await message.answer("На жаль, ми не знайшли жодного квадрокоптера, який би відповідав вашим вимогам.")
    else:
        unique_quadcopters = list(dict.fromkeys(quadcopters))
        for quad in unique_quadcopters:
            response = (
                f"Назва: {quad[1]}, Ціна: {quad[2]} {user_currency}, Час польоту: {quad[3]} хв, Дальність польоту: {quad[4]} m\n"
                f"Опис: {quad[6]}"
            )
            order_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Order", callback_data=f"order_{quad[0]}")]
            ])

            await message.answer(response, reply_markup=order_button)

    await state.clear()


@dp.callback_query(lambda c: c.data and c.data.startswith('order_'))
async def process_order_callback(callback_query: types.CallbackQuery):
    quadcopter_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id

    if not is_user_registered(user_id):
        await callback_query.message.answer("Ви ще не зареєстровані. Будь ласка, зареєструйтеся за допомогою команди /register.")
        return


    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM quadcopters WHERE id = ?', (quadcopter_id,))
        quadcopter = cursor.fetchone()
    except Exception as e:
        logging.error(f"Error getting quadcopter {quadcopter_id}: {e}")
        await callback_query.message.answer("Під час отримання інформації про квадрокоптер сталася помилка. Спробуйте ще раз.")
        return
    finally:
        conn.close()

    if not quadcopter:
        await callback_query.message.answer("Квадрокоптер не знайдено. Спробуйте ще раз.")
        return

    quadcopter_name, price = quadcopter[1], quadcopter[2]
    balance = get_user_balance(user_id)

    if balance < price:
        await callback_query.message.answer(f"У вас недостатньо коштів, щоб замовити цей квадрокоптер. Ваш баланс: {balance} UAH. Будь ласка, поповніть свій баланс за допомогою команди /topup.")
        return

    try:
        update_user_balance(user_id, -price)
        await callback_query.message.answer(f"Замовлення на квадрокоптер '{quadcopter_name}' успішно розміщено! Ваш новий баланс: {balance - price} UAH.")
    except Exception as e:
        logging.error(f"Error updating balance for user {user_id}: {e}")
        await callback_query.message.answer("An error occurred while processing your payment. Please try again.")
        return

    await cmd_start(callback_query.message)


if __name__ == "__main__":
    init_db()
    asyncio.run(dp.start_polling(bot))
