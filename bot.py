import os
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

TOKEN = os.getenv("TOKEN")

def main_menu():
    keyboard = [[InlineKeyboardButton("🕌 مواقيت الصلوات", callback_data="prayer")],
                [InlineKeyboardButton("💡 اشترك في باقة الفوائد اليومية", callback_data="subscribe_faidah")],
                [InlineKeyboardButton("📖 اشترك في برنامج حفظ الكلمات العلية", callback_data="subscribe_words")]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🌙 مرحبًا في بوت رمضان! اختر من القائمة أدناه:", reply_markup=main_menu())

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "prayer":
        await query.message.edit_text("🔍 أدخل اسم المدينة للحصول على مواقيت الصلاة:")
        context.user_data["awaiting_city"] = True
    elif query.data == "subscribe_faidah":
        await query.message.edit_text("✅ تم الاشتراك في باقة الفوائد اليومية! سيتم إرسال فوائد خلال اليوم والليلة.", reply_markup=back_to_main())
    elif query.data == "subscribe_words":
        keyboard = [[InlineKeyboardButton("كلمة", callback_data="word_1")],
                    [InlineKeyboardButton("كلمتين", callback_data="word_2")]]
        await query.message.edit_text("📖 كم عدد الكلمات التي تريد حفظها؟", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data in ["word_1", "word_2"]:
        await query.message.edit_text("✅ تم الاشتراك في برنامج حفظ الكلمات العلية! سيتم تذكيرك كل يوم بالعصر بكلمة.", reply_markup=back_to_main())
    elif query.data == "back":
        await query.message.edit_text("🌙 مرحبًا في بوت رمضان! اختر من القائمة أدناه:", reply_markup=main_menu())

async def handle_city(update: Update, context: CallbackContext):
    if "awaiting_city" in context.user_data and context.user_data["awaiting_city"]:
        city = update.message.text.strip()
        prayer_times = get_prayer_times(city)
        await update.message.reply_text(prayer_times, reply_markup=back_to_main())
        context.user_data["awaiting_city"] = False

def get_prayer_times(city, country="SA", method=4):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method={method}"
    response = requests.get(url).json()
    if "data" in response:
        timings = response["data"]["timings"]
        hijri_date = response["data"]["date"]["hijri"]["date"]
        prayer_times_text = f"🕌 مواقيت الصلاة في {city} - 📆 {hijri_date}:
"
        for prayer in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]:
            prayer_times_text += f"{prayer}: {timings[prayer]}\n"
        return prayer_times_text
    return "❌ لم يتم العثور على المواقيت، تأكد من اسم المدينة."

def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back")]])

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))
    app.run_polling()

if __name__ == "__main__":
    main()
