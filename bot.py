import os
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
)

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

# حالات المحادثة
MAIN_MENU, CITY_INPUT, DAILY_FAIDAH, MEMORIZE_WORDS, WORD_COUNT = range(5)

# دالة جلب مواقيت الصلاة بناءً على المدينة
def get_prayer_times(city, country="SA", method=4):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method={method}"
    try:
        response = requests.get(url).json()
        if "data" in response:
            timings = response["data"]["timings"]
            hijri_date = response["data"]["date"]["hijri"]["date"]
            prayer_times_text = f"🕌 مواقيت الصلاة في {city}, {country} - 📆 {hijri_date}:\n\n"
            prayer_order = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
            for prayer in prayer_order:
                prayer_times_text += f"{prayer}: {timings[prayer]}\n"
            return prayer_times_text
        return "❌ لم يتم العثور على المواقيت، تأكد من اسم المدينة والدولة."
    except requests.RequestException as e:
        return f"❌ حدث خطأ أثناء جلب المواقيت: {e}"

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("مواقيت الصلوات", callback_data="prayer_times")],
        [InlineKeyboardButton("اشترك في باقة الفوائد اليومية", callback_data="daily_faidah")],
        [InlineKeyboardButton("اشترك في برنامج حفظ الكلمات العلية", callback_data="memorize_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا! اختر من القائمة:", reply_markup=reply_markup)
    return MAIN_MENU

# معالجة اختيار مواقيت الصلوات
async def prayer_times(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🔍 أدخل اسم المدينة للحصول على مواقيت الصلاة:")
    return CITY_INPUT

# معالجة إدخال المدينة
async def city_input(update: Update, context: CallbackContext):
    city = update.message.text.strip()
    prayer_times = get_prayer_times(city)
    keyboard = [[InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(prayer_times, reply_markup=reply_markup)
    return MAIN_MENU

# معالجة اختيار باقة الفوائد اليومية
async def daily_faidah(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "✅ تم الاشتراك في باقة الفوائد اليومية. سيتم إرسال فوائد خلال اليوم والليلة.",
        reply_markup=reply_markup,
    )
    return MAIN_MENU

# معالجة اختيار برنامج حفظ الكلمات العلية
async def memorize_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("كلمة واحدة", callback_data="one_word")],
        [InlineKeyboardButton("كلمتين", callback_data="two_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "كم عدد الكلمات التي تريد حفظها؟", reply_markup=reply_markup
    )
    return WORD_COUNT

# معالجة اختيار عدد الكلمات
async def word_count(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    choice = update.callback_query.data
    if choice == "one_word":
        message = "✅ تم الاشتراك في برنامج حفظ كلمة واحدة يوميًا."
    else:
        message = "✅ تم الاشتراك في برنامج حفظ كلمتين يوميًا."
    keyboard = [[InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    return MAIN_MENU

# الرجوع للقائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("مواقيت الصلوات", callback_data="prayer_times")],
        [InlineKeyboardButton("اشترك في باقة الفوائد اليومية", callback_data="daily_faidah")],
        [InlineKeyboardButton("اشترك في برنامج حفظ الكلمات العلية", callback_data="memorize_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("اختر من القائمة:", reply_markup=reply_markup)
    return MAIN_MENU

# إعداد البوت وتشغيله
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(prayer_times, pattern="^prayer_times$"),
                CallbackQueryHandler(daily_faidah, pattern="^daily_faidah$"),
                CallbackQueryHandler(memorize_words, pattern="^memorize_words$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            CITY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_input)],
            WORD_COUNT: [
                CallbackQueryHandler(word_count, pattern="^one_word$"),
                CallbackQueryHandler(word_count, pattern="^two_words$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
