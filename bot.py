import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters,
)

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

# حالات المحادثة
DAY_SELECTION, MEMORIZE, TEST = range(3)

# النص الأساسي الذي يبدأ به كل يوم
BASE_TEXT = "قال مولانا شمس الزمان الإمام طارق بن محمد السعدي قدس الله سره العلي:"

# قائمة الكلمات لـ 30 يومًا (الجزء بعد "العلي:" فقط)
WORDS = [
    "مقدار رحمة البرية بقدر ما في قلوبهم من المحبة الحية",
    "الصبر مفتاح كل خير",
    "القرآن نور القلوب",
    "الصدقة باب الرحمة",
    "الصلاة عماد الدين",
    "الذكر غذاء الروح",
    "التوبة طريق النجاة",
    "الدعاء سلاح المؤمن",
    "الإخلاص جوهر العمل",
    "رمضان مدرسة التقوى",
    "التقوى زينة العبد",
    "الصمت كنز الحكمة",
    "القلب وعاء الإيمان",
    "الجار مرآة الأخلاق",
    "الأمل شعاع الحياة",
    "الرضا باب السعادة",
    "العمل مفتاح الجنة",
    "الشكر زيادة النعم",
    "العدل أساس الملك",
    "التوكل درع المؤمن",
    "ليلة القدر جوهرة الزمان",
    "العتق من النار غاية الصائم",
    "الاجتهاد سبيل العزة",
    "التهجد نور الليل",
    "الاستغفار مفتاح الفرج",
    "القيام ليلة الإسراء",
    "الإنفاق في سبيل الله",
    "الخشوع روح الصلاة",
    "العيد بهجة الطاعة",
    "رمضان وداع الأرواح",
]

# دمج النص الأساسي مع الكلمات لعرضها عند اختيار اليوم
FULL_WORDS = [f"{BASE_TEXT} {word}" for word in WORDS]

# حفظ بيانات المستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": []}

    context.user_data.clear()
    context.user_data["current_words"] = FULL_WORDS
    await show_days(update, context)
    return DAY_SELECTION

async def show_days(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    words = context.user_data["current_words"]

    keyboard = []
    for i in range(0, 30, 3):
        row = [
            InlineKeyboardButton(
                f"اليوم {i+1}{' ✅' if words[i] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i}"
            ),
            InlineKeyboardButton(
                f"اليوم {i+2}{' ✅' if words[i+1] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i+1}"
            ) if i + 1 < len(words) else None,
            InlineKeyboardButton(
                f"اليوم {i+3}{' ✅' if words[i+2] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i+2}"
            ) if i + 2 < len(words) else None,
        ]
        keyboard.append([btn for btn in row if btn])

    if user_data[user_id]["memorized_words"]:
        keyboard.append([InlineKeyboardButton("📖 مراجعة", callback_data="review")])
        keyboard.append([InlineKeyboardButton("📚 اختبار شامل", callback_data="test_all")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "🌙 *رحلة حفظ الكلمات العلية في شهر رمضان المبارك* 🌙\n\n"
        "✨ انطلق في مغامرة يومية مع كلمات الحكمة والمعرفة في شهر الخير\n"
        "📅 اختر اليوم واحفظ الكلمة ثم اضغط *تم الحفظ* 🌟\n"
        "📖 استمتع بمراجعة كنوزك المحفوظة عبر زر *مراجعة* ✨\n"
        "📝 أو تحدَّ نفسك باختبار شامل من خلال زر *اختبار شامل* 🏆"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION

# عرض الكلمة للحفظ أو المراجعة
async def select_day(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    words = context.user_data["current_words"]
    word = words[day_index]

    if word in user_data[user_id]["memorized_words"]:
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("✅ تم الحفظ", callback_data=f"memorize_{day_index}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"📜 *اليوم {day_index + 1}*\n\n{word}",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MEMORIZE

# معالجة الحفظ
async def memorize_word(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    word = context.user_data["current_words"][day_index]

    if word not in user_data[user_id]["memorized_words"]:
        user_data[user_id]["memorized_words"].append(word)

    await update.callback_query.edit_message_text("✅ *تم الحفظ بنجاح!*", parse_mode="Markdown")
    await show_days(update, context)
    return DAY_SELECTION

# مراجعة الكلمات المحفوظة
async def review(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await update.callback_query.edit_message_text(
            "📖 *لم تضف كلمات إلى كنزك بعد!*",
            parse_mode="Markdown"
        )
    else:
        review_text = "📖 *كنوزك المحفوظة:*\n\n" + "\n".join(memorized)
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            review_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    return DAY_SELECTION

# اختبار شامل
async def start_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await update.callback_query.edit_message_text(
            "📚 *لا كلمات محفوظة لاختبارها بعد!*",
            parse_mode="Markdown"
        )
        return DAY_SELECTION

    # استخراج الكلمات الأساسية (بعد "العلي:") للاختبار
    context.user_data["test_words"] = [word.split(BASE_TEXT)[1].strip() for word in memorized]
    context.user_data["last_question"] = None  # لتتبع السؤال السابق
    await ask_next_question(update, context)
    return TEST

async def ask_next_question(update: Update, context: CallbackContext):
    words = context.user_data["test_words"]
    last_question = context.user_data.get("last_question")

    # اختيار كلمة جديدة عشوائيًا مع التأكد من عدم تكرار السؤال السابق إذا أمكن
    word_phrase = random.choice(words)
    while words and len(words) > 1 and last_question and last_question["q"].split(" ")[0] in word_phrase:
        word_phrase = random.choice(words)  # تنويع الكلمات إذا أمكن

    word_parts = word_phrase.split()
    if len(word_parts) < 2:
        question = word_phrase  # إذا كانت كلمة واحدة فقط (نادر)
        correct_answer = word_phrase
    else:
        # اختيار موقع الفراغ عشوائيًا مع التأكد من أنه مختلف عن السابق إذا أمكن
        blank_pos = random.randint(0, len(word_parts) - 1)
        if last_question and len(words) >= 1:
            last_blank_pos = last_question["q"].split().index("ـــــــ")
            while blank_pos == last_blank_pos and len(word_parts) > 1:
                blank_pos = random.randint(0, len(word_parts) - 1)

        correct_answer = word_parts[blank_pos]
        word_parts[blank_pos] = "ـــــــ"
        question = " ".join(word_parts)

    context.user_data["current_question"] = {"q": question, "a": correct_answer}
    context.user_data["last_question"] = {"q": question, "a": correct_answer}  # تخزين السؤال الحالي كآخر سؤال

    await (update.callback_query.edit_message_text if hasattr(update, 'callback_query') and update.callback_query else update.message.reply_text)(
        f"📝 *املأ الفراغ:*\n\n{question}",
        parse_mode="Markdown",
    )

async def handle_test_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    question = context.user_data["current_question"]

    keyboard = [
        [InlineKeyboardButton("➡️ سؤال آخر", callback_data="next_question")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_answer.lower() == question["a"].lower():
        result = "✅ *إجابة صحيحة!*\n\n" + f"الإجابة: {question['a']}"
    else:
        result = f"❌ *إجابة خاطئة!* الإجابة الصحيحة: {question['a']}"

    await update.message.reply_text(result, reply_markup=reply_markup, parse_mode="Markdown")
    return TEST

async def next_question(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await ask_next_question(update, context)
    return TEST

# الرجوع لاختيار اليوم
async def back_to_days(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await show_days(update, context)
    return DAY_SELECTION

# معالجة الكتابة العشوائية وإعادة المستخدم للقائمة الرئيسية
async def handle_text(update: Update, context: CallbackContext):
    current_state = context.user_data.get("state", DAY_SELECTION)
    if current_state != TEST:
        await show_days(update, context)
        return DAY_SELECTION

# إعداد البوت وتشغيله
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DAY_SELECTION: [
                CallbackQueryHandler(select_day, pattern="^day_"),
                CallbackQueryHandler(review, pattern="^review$"),
                CallbackQueryHandler(start_test, pattern="^test_all$"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
            ],
            MEMORIZE: [
                CallbackQueryHandler(memorize_word, pattern="^memorize_"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
            ],
            TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_answer),
                CallbackQueryHandler(next_question, pattern="^next_question$"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
