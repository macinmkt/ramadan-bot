from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import requests
import random
import sqlite3
import os

TOKEN = os.getenv("TOKEN")

# دالة جلب مواقيت الصلاة بناءً على المدينة
def get_prayer_times(city):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country=&method=2"
    response = requests.get(url).json()
    if "data" in response:
        timings = response["data"]["timings"]
        return f"🕌 مواقيت الصلاة في {city}:\n\n" + "\n".join([f"{key}: {value}" for key, value in timings.items()])

" + "\n".join([f"{key}: {value}" for key, value in timings.items()])
    return "❌ لم يتم العثور على المواقيت، تأكد من اسم المدينة."

# دالة استقبال المدينة وإرسال المواقيت
def prayer_command(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 أدخل اسم المدينة للحصول على مواقيت الصلاة:")

def handle_city(update: Update, context: CallbackContext):
    city = update.message.text.strip()
    prayer_times = get_prayer_times(city)
    update.message.reply_text(prayer_times)

# دالة إرسال فائدة عشوائية من قاعدة البيانات
def send_faidah(update: Update, context: CallbackContext):
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM faidah ORDER BY RANDOM() LIMIT 1")
    faidah = cursor.fetchone()
    conn.close()

    if faidah:
        update.message.reply_text(f"💡 {faidah[0]}")
    else:
        update.message.reply_text("❌ لا توجد فوائد متاحة حاليًا.")

# دالة المسابقة
def quiz_command(update: Update, context: CallbackContext):
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM quiz ORDER BY RANDOM() LIMIT 1")
    question = cursor.fetchone()
    conn.close()

    if question:
        context.user_data["answer"] = question[1]
        update.message.reply_text(f"❓ {question[0]}")
    else:
        update.message.reply_text("❌ لا توجد أسئلة متاحة حاليًا.")

# دالة التحقق من الإجابة
def check_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text.strip()
    correct_answer = context.user_data.get("answer", "")

    if user_answer.lower() == correct_answer.lower():
        update.message.reply_text("✅ إجابة صحيحة! تم تسجيلك في السحب.")
        conn = sqlite3.connect("ramadan_bot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO participants (user_id, username, correct_answers) VALUES (?, ?, ?)",
                       (update.message.from_user.id, update.message.from_user.username, 1))
        conn.commit()
        conn.close()
    else:
        update.message.reply_text("❌ إجابة خاطئة، حاول مرة أخرى!")

# دالة اختيار الفائز العشوائي
def pick_winner(update: Update, context: CallbackContext):
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM participants ORDER BY RANDOM() LIMIT 1")
    winner = cursor.fetchone()
    conn.close()

    if winner:
        update.message.reply_text(f"🎉 الفائز لهذا الأسبوع هو: @{winner[0]}! سيتم إرسال الجائزة له.")
    else:
        update.message.reply_text("❌ لا يوجد مشاركين حتى الآن.")

# إعداد الأوامر
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🌙 مرحبًا في بوت رمضان! استخدم /prayer لمواقيت الصلاة، /faidah لفوائد إسلامية، و /quiz للمسابقة.")))
    dp.add_handler(CommandHandler("prayer", prayer_command))
    dp.add_handler(CommandHandler("faidah", send_faidah))
    dp.add_handler(CommandHandler("quiz", quiz_command))
    dp.add_handler(CommandHandler("winner", pick_winner))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_city))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
