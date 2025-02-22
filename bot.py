from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import asyncio
import datetime

TOKEN = "YOUR_BOT_TOKEN"
subscribed_users = {"prayer_times": {}, "daily_fawaid": set(), "word_memorization": {}}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🕌 مواقيت الصلوات", callback_data="prayer_times")],
        [InlineKeyboardButton("📜 اشترك في باقة الفوائد اليومية", callback_data="daily_fawaid")],
        [InlineKeyboardButton("📖 اشترك في برنامج حفظ الكلمات العُلية", callback_data="word_memorization")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("مرحبًا بك في البوت! اختر أحد الخيارات:", reply_markup=main_menu())

async def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "prayer_times":
        await query.message.reply_text("✍️ اكتب اسم مدينتك للحصول على مواقيت الصلاة:")
        context.user_data["awaiting_city"] = True
    elif query.data == "daily_fawaid":
        subscribed_users["daily_fawaid"].add(query.from_user.id)
        await query.message.reply_text("✅ تم الاشتراك في باقة الفوائد اليومية!", reply_markup=main_menu())
    elif query.data == "word_memorization":
        keyboard = [[InlineKeyboardButton("كلمة واحدة", callback_data="word_1"), InlineKeyboardButton("كلمتين", callback_data="word_2")]]
        await query.message.reply_text("📖 كم عدد الكلمات التي تريد حفظها؟", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data in ["word_1", "word_2"]:
        num_words = 1 if query.data == "word_1" else 2
        subscribed_users["word_memorization"][query.from_user.id] = num_words
        await query.message.reply_text(f"✅ تم الاشتراك في برنامج حفظ {num_words} كلمة يوميًا!", reply_markup=main_menu())

async def handle_text(update: Update, context: CallbackContext):
    if context.user_data.get("awaiting_city"):
        city = update.message.text
        context.user_data["awaiting_city"] = False
        prayer_times = get_prayer_times(city)  # تحتاج لدمج API
        if prayer_times:
            await update.message.reply_text(f"🕌 مواقيت الصلاة في {city} \n{prayer_times}", reply_markup=main_menu())
        else:
            await update.message.reply_text("❌ لم أتمكن من جلب مواقيت الصلاة. تأكد من صحة اسم المدينة.")

async def send_reminders():
    while True:
        now = datetime.datetime.now()
        if now.hour == 15 and now.minute == 0:  # وقت العصر
            for user_id, num_words in subscribed_users["word_memorization"].items():
                await application.bot.send_message(user_id, f"📖 كلمتك اليوم: ...")
        if now.weekday() == 4 and now.hour == 14 and now.minute == 0:  # يوم الجمعة قبل العصر
            for user_id in subscribed_users["word_memorization"]:
                await application.bot.send_message(user_id, "🔄 تذكير بجميع الكلمات المحفوظة سابقًا: ...")
        await asyncio.sleep(60)  # التحقق كل دقيقة

def get_prayer_times(city):
    return "🕋 الفجر: 5:00 ص، الظهر: 12:30 م، العصر: 3:45 م، المغرب: 6:15 م، العشاء: 8:00 م"

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_buttons))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

loop = asyncio.get_event_loop()
loop.create_task(send_reminders())
application.run_polling()
