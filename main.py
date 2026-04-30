import asyncio
import requests
import io
import random
import os
from PIL import Image
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (BufferedInputFile, LabeledPrice, PreCheckoutQuery, 
                           ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiohttp import web

# --- НАСТРОЙКИ (Вставь свой токен здесь) ---
API_TOKEN = '8591021129:AAH1tpaNlpkiUsYCm-IwEhHqp5wYN-bvW1w'
CAT_API_KEY = 'live_ZR1ZAaKHkb5nkw48XEReMAdjNEOdKbk65WtAVAHlkcEJ2wNQE8NXMiARYspuZLga'
BOT_USERNAME = 'your_catier_bot' # Юзернейм твоего бота без @
ADMIN_USERNAME = 'angelovSasha'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Переменные режима
TEST_MODE = False
EMOJI_LIST = ["🐱", "🐈", "😻", "🐾", "😼", "😺", "😸", "😽"]

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Чтобы не было ошибок порта) ---
async def handle(request):
    return web.Response(text="Catier Bot is Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render сам назначит порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 10000)) 
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- КНОПКИ ---
def main_kb():
    kb = [[KeyboardButton(text="Получить котика 🐾")],
          [KeyboardButton(text="Мой стикерпак 🔗"), KeyboardButton(text="Инструкция 📖")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ЛОГИКА КОТОВ ---
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот Catier. Давай создавать твой пак!", reply_markup=main_kb())

@dp.message(F.text == "Инструкция 📖")
async def send_instruction(message: types.Message):
    text = (
        "<b>Инструкция по обновлению:</b>\n\n"
        "1. Нажми 'Мой стикерпак'.\n"
        "2. Удали старый пак у себя (три точки -> Удалить).\n"
        "3. Перейди по ссылке и добавь обновленный пак.\n\n"
        "Так новые котики появятся в списке!"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "Мой стикерпак 🔗")
async def send_pack_link(message: types.Message):
    pack_link = f"https://t.me/addstickers/c{message.from_user.id}_v3_by_{BOT_USERNAME}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть пак 🐈", url=pack_link)]])
    await message.answer("Твоя персональная ссылка на стикеры:", reply_markup=kb)

@dp.message(F.text == "Получить котика 🐾")
async def get_cat_req(message: types.Message):
    if TEST_MODE or message.from_user.username == ADMIN_USERNAME:
        await add_cat_to_user(message)
    else:
        # Инвойс на Telegram Stars
        await message.answer_invoice(
            title="Новый Котик 🐾", 
            description="Добавление 1 уникального кота в твой пак", 
            prices=[LabeledPrice(label="XTR", amount=5)], 
            payload="cat_payment", 
            currency="XTR", 
            provider_token=""
        )

async def add_cat_to_user(message: types.Message):
    user_id = message.from_user.id
    pack_name = f"c{user_id}_v3_by_{BOT_USERNAME}"
    sticker_bytes = await get_processed_cat_data()
    input_file = BufferedInputFile(sticker_bytes, filename="cat.png")
    try:
        await bot.add_sticker_to_set(user_id=user_id, name=pack_name, 
                                     sticker=types.InputSticker(sticker=input_file, emoji_list=[random.choice(EMOJI_LIST)], format="static"))
    except:
        await bot.create_new_sticker_set(user_id=user_id, name=pack_name, title=f"Cats by {message.from_user.first_name}",
                                         stickers=[types.InputSticker(sticker=input_file, emoji_list=["🐱"], format="static")],
                                         sticker_format="static")
    await message.answer("Котик добавлен! Проверь свой пак.")

@dp.pre_checkout_query()
async def pre_check(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def pay_ok(message: types.Message):
    await add_cat_to_user(message)

# --- ГЛАВНЫЙ ЗАПУСК ---
async def main():
    # Запускаем веб-сервер в фоне для Render
    asyncio.create_task(start_web_server())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
