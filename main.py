from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я-твой помощник по играм в Steam.\nЧтобы начать, введи название игры после команды /game.")


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши название игры после команды.")
        return

    user_input = " ".join(context.args)
    await update.message.reply_text("Секунду, ищу игру ...🚀")

    try:
        search_url = "https://store.steampowered.com/api/storesearch"
        search_params = {"term": user_input, "l": "english", "cc": "RU"}
        search_response = requests.get(search_url, params=search_params).json()

        if search_response.get("items"):
            appid = str(search_response["items"][0]["id"])
        else:
            await update.message.reply_text("По такому названию ничего не найдено.")
            return

        url = "https://store.steampowered.com/api/appdetails"
        response = requests.get(url, params={"appids": appid, "l": "russian", "cc": "ru"})
        data = response.json()

        info = data.get(appid, {})
        if not info.get("success"):
            await update.message.reply_text("Не удалось получить данные об игре.")
            return

        game_data = info["data"]
        name = game_data.get("name", "Название скрыто")
        description = game_data.get("short_description", "Описание отсутствует")
        image_url = game_data.get("header_image")

        recommendations = game_data.get("recommendations")
        if recommendations:
            total_reviews = recommendations.get("total", 0)
            review_text = f"⭐ Отзывов: {total_reviews}"
        else:
            review_text = "⭐ Отзывов пока нет"

        is_free = game_data.get("is_free", False)
        if is_free:
            price_text = "💰 Бесплатно"
        else:
            prices = []
            countries = [{"cc": "ru", "flag": "🇷🇺"}, {"cc": "us", "flag": "🇺🇸"}, {"cc": "ua", "flag": "🇺🇦"}]
            for country in countries:
                country_url = "https://store.steampowered.com/api/appdetails"
                country_params = {"appids": appid, "l": "russian", "cc": country["cc"]}
                country_response = requests.get(country_url, params=country_params).json()
                country_data = country_response.get(appid, {}).get("data", {})
                country_price_info = country_data.get("price_overview")

                if country_price_info:
                    price = country_price_info.get("final_formatted")
                    discount = country_price_info.get("discount_percent", 0)
                    if discount > 0:
                        prices.append(f"{country['flag']} {price} (-{discount}%)")
                    else:
                        prices.append(f"{country['flag']} {price}")

            if prices:
                price_text = "💰 Цены: " + " | ".join(prices)
            else:
                price_text = "💰 Цена не указана"

        final_text = f"<b>🎮 {name}</b>\n\n{price_text}\n━━━━━━━━━━━━━━━\n\n{description}"

        keyboard = [[
            InlineKeyboardButton("🏆 Достижения", callback_data=f"ach_{appid}"),
            InlineKeyboardButton("⭐ Отзывы", callback_data=f"rev_{appid}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if image_url:
            await update.message.reply_photo(
                photo=image_url,
                caption=final_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                final_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("⚠️ Упс! Произошла ошибка при запросе к Steam. Попробуй позже.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("ach_"):
        await query.message.reply_text("🏆 Здесь будет список достижений (мы добавим его позже).")
    elif data.startswith("rev_"):
        await query.message.reply_text("⭐ Здесь будут отзывы (мы добавим их позже).")


def main():
    if not TOKEN:
        raise RuntimeError("Переменная окружения TOKEN не задана")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен! Иди в Telegram и напиши ему.")
    app.run_polling()


if __name__ == "__main__":
    main()