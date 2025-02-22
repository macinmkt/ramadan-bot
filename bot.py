import asyncio
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "TOKEN"

# تفعيل نظام التسجيل لتتبع الأخطاء
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# قائمة المستخدمين المشتركين في الفوائد اليومية والكلمات العلية
subscribed_fawaid = set()
subscribed_words = {}

# دالة القائمة الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🕌 مواقيت الصلاة", callback_data="prayer_times")],
        [InlineKeyboardButton("📚 اشترك في باقة الفوائد اليومية", callback_data="subscribe_fawaid")],
        [InlineKeyboardButton("🔠 اشترك في برنامج حفظ الكلمات العلية", callback_data="subscribe_words")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 مرحبًا! اختر من القائمة:", reply_markup=reply_markup)

# التعامل مع ضغط الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "prayer_times":
        await query.message.reply_text("✍️ اكتب اسم مدينتك للحصول على مواقيت الصلاة.")
        context.user_data["awaiting_city"] = True

    elif query.data == "subscribe_fawaid":
        subscribed_fawaid.add(query.from_user.id)
        await query.message.reply_text("✅ تم الاشتراك في باقة الفوائد اليومية!", reply_markup=main_menu())

    elif query.data == "subscribe_words":
        keyboard = [
            [InlineKeyboardButton("كلمة واحدة", callback_data="word_1")],
            [InlineKeyboardButton("كلمتان", callback_data="word_2")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("🔠 كم عدد الكلمات التي تريد حفظها؟", reply_markup=reply_markup)

    elif query.data in ["word_1", "word_2"]:
        num_words = 1 if query.data == "word_1" else 2
        subscribed_words[query.from_user.id] = num_words
        await query.message.reply_text("✅ تم الاشتراك في برنامج حفظ الكلمات العلية!", reply_markup=main_menu())

# جلب مواقيت الصلاة
async def get_prayer_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_city"):
        city = update.message.text
        context.user_data["awaiting_city"] = False

        api_url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country=SA"
        response = requests.get(api_url).json()

        if response.get("code") == 200:
            timings = response["data"]["timings"]
            hijri_date = response["data"]["date"]["hijri"]["date"]
            prayer_times_text = (
                f"🕌 مواقيت الصلاة في {city} - 📆 {hijri_date}:\n"
                f"🌅 الفجر: {timings['Fajr']}\n"
                f"🌞 الشروق: {timings['Sunrise']}\n"
                f"🕌 الظهر: {timings['Dhuhr']}\n"
                f"🌇 العصر: {timings['Asr']}\n"
                f"🌆 المغرب: {timings['Maghrib']}\n"
                f"🌙 العشاء: {timings['Isha']}"
            )
            await update.message.reply_text(prayer_times_text, reply_markup=main_menu())
        else:
            await update.message.reply_text("❌ لم يتم العثور على المدينة. تأكد من كتابة الاسم بشكل صحيح.")

# إرسال الفوائد اليومية
async def send_fawaid():
    while True:
        await asyncio.sleep(6 * 60 * 60)  # كل 6 ساعات
        if subscribed_fawaid:
            message = "📖 فائدة اليوم: تعلم شيئًا جديدًا كل يوم يجعلك تتقدم خطوة نحو النجاح!"
            for user_id in subscribed_fawaid:
                try:
                    await app.bot.send_message(chat_id=user_id, text=message)
                except Exception as e:
                    logging.error(f"خطأ في إرسال الفائدة للمستخدم {user_id}: {e}")

# إرسال الكلمات العلية
async def send_words():
    while True:
        now = datetime.now()
        await asyncio.sleep(60)  # تحقق كل دقيقة

        # إرسال كلمة يومية كل يوم العصر
        if now.hour == 15 and now.minute == 0:
            for user_id, num_words in subscribed_words.items():
                words = ["الصدق", "الإخلاص", "الأمانة", "الصبر", "الكرم"]
                message = f"🔠 كلمتك اليوم: {' - '.join(words[:num_words])}"
                try:
                    await app.bot.send_message(chat_id=user_id, text=message)
                except Exception as e:
                    logging.error(f"خطأ في إرسال الكلمة {user_id}: {e}")

        # تذكير أسبوعي يوم الجمعة
        if now.weekday() == 4 and now.hour == 14 and now.minute == 0:
            for user_id in subscribed_words:
                try:
                    await app.bot.send_message(chat_id=user_id, text="📚 تذكير: هذه هي الكلمات التي حفظتها خلال الأسبوع! استمر في المراجعة. 💡")
                except Exception as e:
                    logging.error(f"خطأ في التذكير الأسبوعي {user_id}: {e}")

# إنشاء زر الرجوع للقائمة الرئيسية
def main_menu():
    keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

# إرجاع المستخدم للقائمة الرئيسية
async def return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔙 تم الرجوع إلى القائمة الرئيسية.", reply_markup=main_menu())

# تشغيل البوت
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_prayer_times))
app.add_handler(CallbackQueryHandler(return_to_main_menu, pattern="main_menu"))

# تشغيل مهام الإرسال التلقائي
async def main():
    asyncio.create_task(send_fawaid())
    asyncio.create_task(send_words())
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
