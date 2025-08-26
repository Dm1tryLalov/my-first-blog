from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from flask import Flask, request
import asyncio

app = Flask(__name__)

BOT_TOKEN = "8390374974:AAHCvCO74H-QcUqE6o2VCk6BDs5Ewb5yaQ4"

# Состояния для диалога
CHOOSING, SALARY, DAYS_M, DAYS_F, DAYS_15, DAYS_31 = range(6)

# Создаем application один раз при запуске
application = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["1 - За весь месяц", "2 - 25 числа"], ["3 - 10 числа"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )

    await update.message.reply_text(
        "💰 Калькулятор заработной платы\n\n"
        "Выберите вариант расчета:\n"
        "1 - Узнать суммарное начисление за месяц\n"
        "2 - Узнать начисление 25 числа\n"
        "3 - Узнать начисление 10 числа\n\n"
        "Просто нажмите на нужную кнопку ниже:",
        reply_markup=reply_markup,
    )
    return CHOOSING


async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice_text = update.message.text
    if "1" in choice_text:
        context.user_data["choice"] = 1
    elif "2" in choice_text:
        context.user_data["choice"] = 2
    elif "3" in choice_text:
        context.user_data["choice"] = 3
    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из предложенных")
        return CHOOSING

    await update.message.reply_text("Введите ваш оклад (руб):")
    return SALARY


async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["salary"] = float(update.message.text)
        choice = context.user_data["choice"]

        if choice == 1:
            await update.message.reply_text("Сколько рабочих дней в месяце?")
            return DAYS_M
        elif choice == 2:
            await update.message.reply_text("Сколько рабочих дней с 1 по 15 число?")
            return DAYS_15
        elif choice == 3:
            await update.message.reply_text("Сколько рабочих дней с 1 по 30/31 число?")
            return DAYS_31
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число для оклада:")
        return SALARY


async def get_days_m(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["day_m"] = float(update.message.text)
        await update.message.reply_text("Сколько дней вы отработали?")
        return DAYS_F
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return DAYS_M


async def get_days_15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["day_15"] = float(update.message.text)
        await update.message.reply_text("Сколько дней из них вы отработали?")
        return DAYS_F
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return DAYS_15


async def get_days_31(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["day_31"] = float(update.message.text)
        await update.message.reply_text("Сколько дней из них вы отработали?")
        return DAYS_F
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return DAYS_31


async def get_days_f(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days_f = float(update.message.text)
        choice = context.user_data["choice"]
        salary = context.user_data["salary"]
        ndfl = salary * 0.13

        if choice == 1:
            day_m = context.user_data["day_m"]
            result = salary / day_m * days_f - ndfl
            text = "за месяц"
        elif choice == 2:
            day_15 = context.user_data["day_15"]
            result = salary / day_15 * days_f - ndfl
            text = "25 числа"
        elif choice == 3:
            day_31 = context.user_data["day_31"]
            result = salary / day_31 * days_f - ndfl
            text = "10 числа"

        await update.message.reply_text(
            f"💰 Результат расчета {text}:\n"
            f"• Оклад: {salary:.0f} руб.\n"
            f"• НДФЛ: {ndfl:.0f} руб.\n"
            f"• Итого: {result:.0f} руб.\n\n"
            f"Для нового расчета: /start"
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return DAYS_F


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчет отменен")
    return ConversationHandler.END


# Настраиваем обработчики
def setup_handlers():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_salary)],
            DAYS_M: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_days_m)],
            DAYS_15: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_days_15)],
            DAYS_31: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_days_31)],
            DAYS_F: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_days_f)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)


# Инициализируем обработчики при запуске
setup_handlers()


# Обработчик вебхука
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Получаем обновление от Telegram
        update = Update.de_json(request.get_json(), application.bot)

        # Обрабатываем обновление асинхронно
        async def process_update():
            await application.process_update(update)

        # Запускаем асинхронную обработку
        asyncio.run(process_update())

        return "", 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return "", 200


# Главная страница для проверки
@app.route("/")
def home():
    return "💰 Калькулятор заработной платы работает! Используйте /start в Telegram"


# Установка вебхука при запуске
@app.before_first_request
def set_webhook():
    # Замените yourusername на ваш логин PythonAnywhere
    webhook_url = f"https://dimalalov.pythonanywhere.com/webhook"

    # Устанавливаем вебхук
    application.bot.set_webhook(webhook_url)
    print(f"Вебхук установлен: {webhook_url}")


if __name__ == "__main__":
    app.run(debug=True)
