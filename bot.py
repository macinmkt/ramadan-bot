import requests
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")

# تخزين بيانات المستخدمين
users_data = {}

# دالة جلب مواقيت الصلاة
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

# دالة إرسال فائدة عشوائية
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

# دالة المسابقة
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

# دالة التحقق من الإجابة
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

# ====== ميزة السبحة الإلكترونية ======
async def tasbeeh_menu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    users_data[user_id] = {"count": 0, "goal": None}

    keyboard = [
        [InlineKeyboardButton("📿 اضف عدد", callback_data='add_count')],
        [InlineKeyboardButton("🔔 حدد تنبيه", callback_data='set_alert')],
        [InlineKeyboardButton("🔄 تصفير العداد", callback_data='reset')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📿 اختر إعدادات التسبيح:", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "add_count":
        await context.bot.send_message(chat_id=user_id, text="🔢 أدخل عدد التسبيحات:")
        context.user_data["waiting_for_count"] = True

    elif query.data == "set_alert":
        await context.bot.send_message(chat_id=user_id, text="🔔 أدخل العدد الذي تريد تلقي تنبيه عنده:")
        context.user_data["waiting_for_alert"] = True

    elif query.data == "reset":
        users_data[user_id] = {"count": 0, "goal": None}
        await query.message.edit_text("🔄 تم تصفير العداد!")

async def handle_tasbeeh_input(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if "waiting_for_count" in context.user_data:
        try:
            count = int(text)
            users_data[user_id]["count"] = count
            del context.user_data["waiting_for_count"]
            await update.message.reply_text(f"✅ تم ضبط العداد على {count} تسبيحة.")
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح.")

    elif "waiting_for_alert" in context.user_data:
        try:
            goal = int(text)
            users_data[user_id]["goal"] = goal
            del context.user_data["waiting_for_alert"]
            await update.message.reply_text(f"🔔 سيتم تنبيهك عند الوصول إلى {goal} تسبيحة.")
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح.")

async def tasbeeh(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in users_data:
        users_data[user_id] = {"count": 0, "goal": None}

    users_data[user_id]["count"] += 1
    count = users_data[user_id]["count"]
    goal = users_data[user_id]["goal"]

    if goal and count >= goal:
        await update.message.reply_text(f"🤲 وصلت إلى {goal} تسبيحة! نسأل الله أن يتقبل منك. 🤲")
    else:
        await update.message.reply_text(f"📿 عدد التسبيحات الحالي: {count}")

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", tasbeeh_menu))
    app.add_handler(CommandHandler("tasbeeh", tasbeeh))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tasbeeh_input))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()
