from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
import dotenv
from dotenv import load_dotenv

# Твой токен от BotFather
TOKEN = "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"

load_dotenv()
TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот.\nНапиши /game 730 (по ID) или /game portal (по названию).")

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши ID или название игры после команды. Пример: /game portal 2")
        return
    
    # Собираем всё, что написал пользователь (на случай, если он написал "portal 2")
    user_input = " ".join(context.args)
    appid = None

    # Если пользователь ввел цифры (ID)
    if user_input.isdigit():
        appid = user_input
        await update.message.reply_text(f"Ищу игру по ID {appid}...")
    else:
        # Если ввел текст, идем в поиск Steam
        await update.message.reply_text(f"Ищу игру по названию '{user_input}'...")
        search_url = "https://store.steampowered.com/api/storesearch"
        search_params = {"term": user_input, "l": "russian", "cc": "RU"}
        
        search_response = requests.get(search_url, params=search_params).json()
        
        if search_response.get("items"):
            # Берем первую игру из списка результатов
            appid = str(search_response["items"][0]["id"])
        else:
            await update.message.reply_text("По такому названию ничего не найдено.")
            return

    # Теперь у нас есть appid, и мы запрашиваем полную инфу
    url = "https://store.steampowered.com/api/appdetails"
    response = requests.get(url, params={"appids": appid, "l": "russian"})
    data = response.json()

    info = data.get(appid, {})
    if not info.get("success"):
        await update.message.reply_text("Не удалось получить данные об игре.")
        return

    game_data = info["data"]
    name = game_data.get("name", "Прошу прощения, но название игры не найдено.")
    description = game_data.get("short_description", "Описание отсутствует")
    image_url = game_data.get("header_image")

    if image_url:
        await update.message.reply_photo(photo=image_url, caption=f"🎮: {name}\n\n {description}")
    else:
        await update.message.reply_text(f"🎮: {name}\n\n {description}")    

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game))
    
    print("Бот запущен! Иди в Telegram и напиши ему.")
    app.run_polling()

if __name__ == "__main__":
    main()