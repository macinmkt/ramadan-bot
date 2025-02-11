import requests
import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")

# دالة جلب مواقيت الصلاة بناءً على المدينة
def get_prayer_times(city, country="SA", method=4):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method={method}"
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

# دالة استقبال المدينة وإرسال المواقيت
async def prayer_command(update: Update, context: CallbackContext):
    await update.message.reply_text("🔍 أدخل اسم المدينة للحصول على مواقيت الصلاة:")

async def handle_city(update: Update, context: CallbackContext):
    city = update.message.text.strip()
    prayer_times = get_prayer_times(city, country="SA", method=4)
    await update.message.reply_text(prayer_times)

# دالة إرسال فائدة عشوائية من قاعدة البيانات
async def send_faidah(update: Update, context: CallbackContext):
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM faidah ORDER BY RANDOM() LIMIT 1")
    faidah = cursor.fetchone()
    conn.close()

    if faidah:
        await update.message.reply_text(f"💡 {faidah[0]}")
    else:
        await update.message.reply_text("❌ لا توجد فوائد متاحة حاليًا.")

# دالة المسابقة الإسلامية
async def quiz_command(update: Update, context: CallbackContext):
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM quiz ORDER BY RANDOM() LIMIT 1")
    question = cursor.fetchone()
    conn.close()

    if question:
        context.user_data["answer"] = question[1]
        await update.message.reply_text(f"❓ {question[0]}")
    else:
        await update.message.reply_text("❌ لا توجد أسئلة متاحة حاليًا.")

# دالة التحقق من إجابة المستخدم
async def check_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text.strip()
    correct_answer = context.user_data.get("answer", "")

    if user_answer.lower() == correct_answer.lower():
        await update.message.reply_text("✅ إجابة صحيحة! تم تسجيلك في السحب.")
        
        conn = sqlite3.connect("ramadan_bot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO participants (user_id, username, correct_answers) VALUES (?, ?, ?)",
                       (update.message.from_user.id, update.message.from_user.username, 1))
        conn.commit()
        conn.close()
    else:
        await update.message.reply_text("❌ إجابة خاطئة، حاول مرة أخرى!")

# دالة اختيار الفائز العشوائي
async def pick_winner(update: Update, context: CallbackContext):
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM participants ORDER BY RANDOM() LIMIT 1")
    winner = cursor.fetchone()
    conn.close()

    if winner:
        await update.message.reply_text(f"🎉 الفائز لهذا الأسبوع هو: @{winner[0]}! سيتم إرسال الجائزة له.")
    else:
        await update.message.reply_text("❌ لا يوجد مشاركون حتى الآن.")

# إعداد البوت وتشغيله
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text(
        "🌙 مرحبًا في بوت رمضان!\n"
        "🕌 استخدم /prayer لمواقيت الصلاة\n"
        "💡 استخدم /faidah للحصول على فائدة\n"
        "❓ استخدم /quiz للمشاركة في المسابقة\n"
        "🏆 استخدم /winner لاختيار الفائز الأسبوعي"
    )))

    app.add_handler(CommandHandler("prayer", prayer_command))
    app.add_handler(CommandHandler("faidah", send_faidah))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("winner", pick_winner))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
