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

# --- НАСТРОЙКИ ---
API_TOKEN = '8591021129:AAGXFaUnu3scHy_bTObqOuToq73hJp6dTlI'
CAT_API_KEY = 'live_ZR1ZAaKHkb5nkw48XEReMAdjNEOdKbk65WtAVAHlkcEJ2wNQE8NXMiARYspuZLga'
BOT_USERNAME = 'your_catier_bot' # Укажи юзернейм своего бота без @
ADMIN_USERNAME = 'angelovSasha'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище данных (в памяти)
user_languages = {} # {user_id: 'ru'/'en'}
active_promocodes = {'CATS_V1': 1} # {код: количество котиков}

# Переменные режима
TEST_MODE = False
EMOJI_LIST = ["🐱", "🐈", "😻", "🐾", "😼", "😺", "😸", "😽"]

# --- МИНИ-ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Catier Bot is Alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ЯЗЫКИ И ТЕКСТЫ ---
TEXTS = {
    'ru': {
        'welcome': "Привет, Александр! Бот готов. Будем создавать твой идеальный пак с котиками?",
        'get_cat': "Получить котика 🐾",
        'my_pack': "Мой стикерпак 🔗",
        'instruction': "Инструкция 📖",
        'promo': "Промокод 🎁",
        'lang': "Язык 🌐",
        'inst_text': (
            "<b>Инструкция по обновлению:</b>\n\n"
            "1. Нажми <b>'Мой стикерпак 🔗'</b>.\n"
            "2. Перейди по ссылке в Телеграм.\n"
            "3. Три точки -> <b>'Удалить'</b> (удали у себя!).\n"
            "4. Зайди в бота, снова нажми 'Мой стикерпак' и добавь его.\n\n"
            "После этого новые котики появятся в твоем списке!"
        ),
        'choose_lang': "Выберите язык / Choose language:",
        'lang_changed': "Язык изменен на Русский 🇷🇺",
        'invoice_title': "Новый Котик 🐾",
        'invoice_desc': "Добавление 1 уникального кота в твой пак",
        'pack_opening': "Открываем твой пак... Подожди секунду.",
        'enter_promo': "Введи промокод (просто напиши его сообщением):",
        'promo_ok': "Промокод принят! Добавляю {} котиков в твой пак.",
        'promo_fail': "Такой промокод не найден или уже использован.",
        'cat_added': "Котик добавлен! Проверь свой пак."
    },
    'en': {
        'welcome': "Hello! Bot is ready. Let's create your perfect cat sticker pack!",
        'get_cat': "Get a Cat 🐾",
        'my_pack': "My Sticker Pack 🔗",
        'instruction': "Instruction 📖",
        'promo': "Promocode 🎁",
        'lang': "Language 🌐",
        'inst_text': (
            "<b>Update Instruction:</b>\n\n"
            "1. Click <b>'My Sticker Pack 🔗'</b>.\n"
            "2. Follow the link to Telegram.\n"
            "3. Three dots -> <b>'Delete'</b> (delete it for yourself).\n"
            "4. Come back to the bot, click 'My Sticker Pack' and add it again.\n\n"
            "New cats will appear in your sticker list!"
        ),
        'choose_lang': "Select language:",
        'lang_changed': "Language changed to English 🇺🇸",
        'invoice_title': "New Cat 🐾",
        'invoice_desc': "Add 1 unique cat to your pack",
        'pack_opening': "Opening your pack... One moment.",
        'enter_promo': "Enter promocode (just send it as a message):",
        'promo_ok': "Promocode accepted! Adding {} cats to your pack.",
        'promo_fail': "Promocode not found or already used.",
        'cat_added': "Cat added! Check your pack."
    }
}

def get_txt(user_id, key):
    lang = user_languages.get(user_id, 'ru')
    return TEXTS[lang].get(key, 'Error: Text not found')

# --- КНОПКИ ---
def main_kb(user_id):
    lang = user_languages.get(user_id, 'ru')
    kb = [[KeyboardButton(text=TEXTS[lang]['get_cat'])],
          [KeyboardButton(text=TEXTS[lang]['my_pack']), KeyboardButton(text=TEXTS[lang]['instruction'])],
          [KeyboardButton(text=TEXTS[lang]['promo']), KeyboardButton(text=TEXTS[lang]['lang'])]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def lang_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Русский 🇷🇺", callback_data="set_lang_ru"),
        InlineKeyboardButton(text="English 🇺🇸", callback_data="set_lang_en")
    ]])
    return kb

# --- КОШАЧЬЯ МАГИЯ ---
async def get_processed_cat_data():
    headers = {'x-api-key': CAT_API_KEY}
    response = requests.get(f'https://api.thecatapi.com/v1/images/search?{random.random()}', headers=headers)
    if response.status_code != 200: return None
    cat_url = response.json()[0]['url']
    img_data = requests.get(cat_url).content
    img = Image.open(io.BytesIO(img_data))
    img.thumbnail((512, 512))
    out_buffer = io.BytesIO()
    img.save(out_buffer, format='PNG')
    out_buffer.seek(0)
    return out_buffer.getvalue()

# --- ЛОГИКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(get_txt(message.from_user.id, 'welcome'), reply_markup=main_kb(message.from_user.id))

@dp.message(F.text == "Язык 🌐")
async def lang_cmd(message: types.Message):
    await message.answer(get_txt(message.from_user.id, 'choose_lang'), reply_markup=lang_kb())

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(query: types.CallbackQuery):
    lang = query.data.split("_")[2]
    user_languages[query.from_user.id] = lang
    await query.message.edit_text(TEXTS[lang]['lang_changed'])
    await query.message.answer(TEXTS[lang]['welcome'], reply_markup=main_kb(query.from_user.id))

@dp.message(F.text == "Инструкция 📖")
@dp.message(F.text == "Instruction 📖")
async def send_instruction(message: types.Message):
    await message.answer(get_txt(message.from_user.id, 'inst_text'), parse_mode="HTML")

@dp.message(F.text == "Мой стикерпак 🔗")
@dp.message(F.text == "My Sticker Pack 🔗")
async def send_pack_link(message: types.Message):
    user_id = message.from_user.id
    pack_name = f"c{user_id}_v3_by_{BOT_USERNAME}"
    await message.answer(get_txt(user_id, 'pack_opening'))
    
    # Пытаемся получить информацию о паке
    pack_link = f"https://t.me/addstickers/{pack_name}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть пак 🐈", url=pack_link)]])
    
    # Бот сначала пытается проверить пак, чтобы не было ошибки
    try:
        await bot.get_sticker_set(name=pack_name)
        await message.answer(get_txt(user_id, 'pack_link'), reply_markup=kb)
    except:
        # Если пак не найден — предлагаем получить кота, чтобы его создать
        await message.answer("Стикерпак еще не создан. Нажмите 'Получить котика 🐾', чтобы создать его!")

@dp.message(F.text == "Получить котика 🐾")
@dp.message(F.text == "Get a Cat 🐾")
async def get_cat_req(message: types.Message):
    user_id = message.from_user.id
    if TEST_MODE or message.from_user.username == ADMIN_USERNAME:
        await message.answer("🛠 Режим админа: добавляю котика бесплатно.")
        await add_cat_to_user(message, count=1)
    else:
        # Инвойс
        await message.answer_invoice(
            title=get_txt(user_id, 'invoice_title'), description=get_txt(user_id, 'invoice_desc'),
            prices=[LabeledPrice(label="XTR", amount=5)], payload="cat_payment", currency="XTR", provider_token=""
        )

# Функция добавления (для оплаты и промокодов)
async def add_cat_to_user(message: types.Message, count=1):
    user_id = message.from_user.id
    pack_name = f"c{user_id}_v3_by_{BOT_USERNAME}"
    
    for _ in range(count):
        sticker_bytes = await get_processed_cat_data()
        if not sticker_bytes: continue
        input_file = BufferedInputFile(sticker_bytes, filename="cat.png")
        input_sticker = types.InputSticker(sticker=input_file, emoji_list=[random.choice(EMOJI_LIST)], format="static")
        try:
            await bot.add_sticker_to_set(user_id=user_id, name=pack_name, sticker=input_sticker)
        except:
            await bot.create_new_sticker_set(
                user_id=user_id, name=pack_name, title=f"Cats by {message.from_user.first_name}",
                stickers=[input_sticker], sticker_format="static"
            )
            break # После создания добавляем только одного, чтобы не было конфликтов
    
    await message.answer(get_txt(user_id, 'cat_added'), reply_markup=main_kb(user_id))

# --- ПЛАТЕЖИ ---
@dp.pre_checkout_query()
async def pre_check(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def pay_ok(message: types.Message):
    await add_cat_to_user(message, count=1)

# --- ПРОМОКОДЫ ---
@dp.message(F.text == "Промокод 🎁")
@dp.message(F.text == "Promocode 🎁")
async def promo_req(message: types.Message):
    await message.answer(get_txt(message.from_user.id, 'enter_promo'), reply_markup=types.ForceReply())

# Проверка промокода (простое текстовое сообщение)
@dp.message(lambda m: m.text in active_promocodes or m.reply_to_message and m.reply_to_message.text == TEXTS.get(user_languages.get(m.from_user.id, 'ru'), {}).get('enter_promo'))
async def check_promo(message: types.Message):
    user_id = message.from_user.id
    code = message.text.strip().upper()
    
    if code in active_promocodes:
        count = active_promocodes[code]
        await message.answer(get_txt(user_id, 'promo_ok').format(count))
        del active_promocodes[code] # Промокод одноразовый
        await add_cat_to_user(message, count=count)
    else:
        # Если это просто текст, а не промокод — игнорим
        if not message.reply_to_message: return
        await message.answer(get_txt(user_id, 'promo_fail'))

# --- ЗАПУСК ---
async def main():
    asyncio.create_task(start_web_server())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
