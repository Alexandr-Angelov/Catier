import asyncio
import requests
import io
import random
import os
from datetime import datetime
from PIL import Image
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (BufferedInputFile, LabeledPrice, PreCheckoutQuery, 
                           ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)

# --- НАСТРОЙКИ ---
API_TOKEN = '8591021129:AAH1tpaNlpkiUsYCm-IwEhHqp5wYN-bvW1w'
CAT_API_KEY = 'live_ZR1ZAaKHkb5nkw48XEReMAdjNEOdKbk65WtAVAHlkcEJ2wNQE8NXMiARYspuZLga'
BOT_USERNAME = 'your_catier_bot' # Замени на юзернейм своего бота БЕЗ @
ADMIN_USERNAME = 'angelovSasha'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_languages = {} 
TEST_MODE = False
PROMOCodes = {}
EMOJI_LIST = ["🐱", "🐈", "😻", "🐾", "😼", "😺", "😸", "😽"]

# --- ТЕКСТЫ ---
TEXTS = {
    'ru': {
        'get_cat': "Получить котика 🐾",
        'my_pack': "Мой стикерпак 🔗",
        'instruction': "Инструкция 📖",
        'promo': "Ввести промокод 🎟",
        'link_btn': "Открыть мой пак 🐈",
        'wait': "Подожди 1-2 минуты и котик появится!",
        'buy_desc': "Добавление 1 кота в ваш пак"
    },
    'uk': {
        'get_cat': "Отримати котика 🐾",
        'my_pack': "Мій стікерпак 🔗",
        'instruction': "Інструкція 📖",
        'promo': "Ввести промокод 🎟",
        'link_btn': "Відкрити мій пак 🐈",
        'wait': "Зачекай 1-2 хвилини і котик з'явиться!",
        'buy_desc': "Додавання 1 кота у ваш пак"
    }
}

def main_kb(lang):
    t = TEXTS.get(lang, TEXTS['ru'])
    kb = [[KeyboardButton(text=t['get_cat'])],
          [KeyboardButton(text=t['my_pack']), KeyboardButton(text=t['instruction'])],
          [KeyboardButton(text=t['promo'])]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_processed_cat_data():
    headers = {'x-api-key': CAT_API_KEY}
    response = requests.get(f'https://api.thecatapi.com/v1/images/search?{random.random()}', headers=headers)
    cat_url = response.json()[0]['url']
    img_data = requests.get(cat_url).content
    img = Image.open(io.BytesIO(img_data))
    img.thumbnail((512, 512))
    out_buffer = io.BytesIO()
    img.save(out_buffer, format='PNG')
    out_buffer.seek(0)
    return out_buffer.getvalue()

# --- АДМИН КОМАНДЫ ---
@dp.message(F.text == "Test Mode On")
async def admin_on(message: types.Message):
    if message.from_user.username == ADMIN_USERNAME:
        global TEST_MODE
        TEST_MODE = True
        await message.answer("🛠 Тестовый режим ВКЛЮЧЕН")

@dp.message(F.text == "Test Mode Off")
async def admin_off(message: types.Message):
    if message.from_user.username == ADMIN_USERNAME:
        global TEST_MODE
        TEST_MODE = False
        await message.answer("💰 Тестовый режим ВЫКЛЮЧЕН")

# --- ЛОГИКА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_languages[message.from_user.id] = 'ru'
    await message.answer("Привет! Я на связи 24/7. Выбери действие:", reply_markup=main_kb('ru'))

@dp.message(F.text.in_(["Инструкция 📖", "Інструкція 📖"]))
async def send_instruction(message: types.Message):
    text = (
        "<b>Что бы получить новых котиков когда вы их купили сделаете следующий шаг :</b>\n\n"
        "1. Зайдите в меню с кнопками.\n"
        "2. Нажмите кнопку <b>'Мой стикерпак'</b>.\n"
        "3. Перейдите в свои стикеры.\n"
        "4. Найдите там стикеры с котами.\n"
        "5. Возле названия нажмите кнопку изменить.\n"
        "6. В открывающемся меню нажмите в правом вверхнем углу на три точки.\n"
        "7. Выберете удалить.\n"
        "8. Нажмите удалить у себя.\n"
        "9. Нажмите на ссылку которую вам отправил бот и нажмите скачать.\n\n"
        "⚠️ <b>ВНИМАНИЕ!</b>\n"
        "Если вы нажмёте 'Удалить у всех', то есть шанс что вы потеряете всех котиков и не сможете вернуть их."
    )
    await message.answer(text, parse_mode="HTML", protect_content=True)

@dp.message(F.text.in_(["Мой стикерпак 🔗", "Мій стікерпак 🔗"]))
async def send_pack_link(message: types.Message):
    lang = user_languages.get(message.from_user.id, 'ru')
    # Добавил префикс 'v2', чтобы избежать ошибки занятого имени
    pack_link = f"https://t.me/addstickers/v2_cat_{message.from_user.id}_by_{BOT_USERNAME}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS[lang]['link_btn'], url=pack_link)]])
    await message.answer("Ваша кнопка на стикерпак:", reply_markup=kb, protect_content=True)

@dp.message(F.text.in_(["Получить котика 🐾", "Отримати котика 🐾"]))
async def get_cat_req(message: types.Message):
    lang = user_languages.get(message.from_user.id, 'ru')
    if TEST_MODE:
        await add_cat_to_user(message, lang)
    else:
        # Для админа тоже шлем инвойс, чтобы ты видел, что оплата работает
        await message.answer_invoice(
            title=TEXTS[lang]['get_cat'], description=TEXTS[lang]['buy_desc'], 
            prices=[LabeledPrice(label="XTR", amount=5)], payload="cat", currency="XTR", provider_token=""
        )

async def add_cat_to_user(message: types.Message, lang):
    user_id = message.from_user.id
    pack_name = f"v2_cat_{user_id}_by_{BOT_USERNAME}"
    sticker_bytes = await get_processed_cat_data()
    input_file = BufferedInputFile(sticker_bytes, filename="cat.png")
    chosen_emoji = random.choice(EMOJI_LIST)
    try:
        await bot.add_sticker_to_set(user_id=user_id, name=pack_name, 
                                     sticker=types.InputSticker(sticker=input_file, emoji_list=[chosen_emoji], format="static"))
        await message.answer(TEXTS[lang]['wait'])
    except Exception:
        await bot.create_new_sticker_set(user_id=user_id, name=pack_name, title=f"Коты {message.from_user.first_name}",
                                         stickers=[types.InputSticker(sticker=input_file, emoji_list=[chosen_emoji], format="static")],
                                         sticker_format="static")
    await message.answer_sticker(sticker=input_file)

@dp.pre_checkout_query()
async def pre_check(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def pay_ok(message: types.Message):
    await add_cat_to_user(message, 'ru')

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
