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
MAIN_MENU, PERIOD_SELECTION, DAY_SELECTION, MEMORIZE, TEST = range(5)

# قوائم الكلمات لكل فترة
WORDS_FIRST_TEN = [
    "الصبر مفتاح الفرج",           # اليوم 1
    "الصوم جنة",                   # اليوم 2
    "القرآن هدى",                  # اليوم 3
    "الصدقة تطفئ الغضب",          # اليوم 4
    "الصلاة نور",                  # اليوم 5
    "الذكر راحة",                  # اليوم 6
    "التوبة مغفرة",                # اليوم 7
    "الدعاء عبادة",               # اليوم 8
    "الإخلاص سر النجاح",          # اليوم 9
    "رمضان فرصة",                 # اليوم 10
]

WORDS_MIDDLE_TEN = [
    "التقوى زاد",                  # اليوم 11
    "الصمت حكمة",                  # اليوم 12
    "القلب مرآة",                  # اليوم 13
    "الجار حق",                    # اليوم 14
    "الأمل قوة",                   # اليوم 15
    "الرضا كنز",                   # اليوم 16
    "العمل صلاح",                 # اليوم 17
    "الشكر نعمة",                  # اليوم 18
    "العدل أساس",                 # اليوم 19
    "التوكل يقين",                 # اليوم 20
]

WORDS_LAST_TEN = [
    "ليلة القدر خير",              # اليوم 21
    "العتق من النار",             # اليوم 22
    "الاجتهاد فضيلة",             # اليوم 23
    "التهجد قربة",                 # اليوم 24
    "الاستغفار مفتاح",            # اليوم 25
    "القيام بركة",                 # اليوم 26
    "الإنفاق ثواب",               # اليوم 27
    "الخشوع راحة",                # اليوم 28
    "العيد فرحة",                  # اليوم 29
    "رمضان وداع",                 # اليوم 30
]

# أسئلة الاختبار لكل فترة
TEST_QUESTIONS = {
    "first_ten": [
        {"q": "ما هو مفتاح الفرج؟", "a": "الصبر"},
        {"q": "ما الذي يطفئ الغضب؟", "a": "الصدقة"},
        {"q": "ما هو نور المؤمن؟", "a": "الصلاة"},
        {"q": "ما هو سر النجاح؟", "a": "الإخلاص"},
        {"q": "ما هي فرصة رمضان؟", "a": "التوبة"},
    ],
    "middle_ten": [
        {"q": "ما هو زاد المؤمن؟", "a": "التقوى"},
        {"q": "ما هو كنز الدنيا؟", "a": "الرضا"},
        {"q": "ما هو أساس العدل؟", "a": "العدل"},
        {"q": "ما هي حكمة الصمت؟", "a": "الصمت"},
        {"q": "ما هو حق الجار؟", "a": "الجار"},
    ],
    "last_ten": [
        {"q": "ما هي خير من ألف شهر؟", "a": "ليلة القدر"},
        {"q": "ما هو مفتاح الاستغفار؟", "a": "الاستغفار"},
        {"q": "ما هي بركة القيام؟", "a": "القيام"},
        {"q": "ما هو ثواب الإنفاق؟", "a": "الإنفاق"},
        {"q": "ما هي فرحة العيد؟", "a": "العيد"},
    ],
    "all_days": [
        {"q": "ما هو مفتاح الفرج؟", "a": "الصبر"},
        {"q": "ما هي خير من ألف شهر؟", "a": "ليلة القدر"},
        {"q": "ما هو زاد المؤمن؟", "a": "التقوى"},
        {"q": "ما هو نور المؤمن؟", "a": "الصلاة"},
        {"q": "ما هو كنز الدنيا؟", "a": "الرضا"},
    ]
}

# حفظ بيانات المستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": [], "points": 0}

    welcome_message = (
        "🌙 *رمضان كريم* 🌙\n\n"
        "مرحبًا بك في بوت مسابقة حفظ الكلمات العلية! اختر من القائمة:"
    )

    keyboard = [
        [InlineKeyboardButton("🕌 مسابقة حفظ الكلمات العلية", callback_data="memorize_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

# اختيار الفترة
async def memorize_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("العشر الأوائل من رمضان", callback_data="first_ten")],
        [InlineKeyboardButton("العشر الوسطى من رمضان", callback_data="middle_ten")],
        [InlineKeyboardButton("العشر الأواخر من رمضان", callback_data="last_ten")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🌙 *اختر الفترة* 🌙",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return PERIOD_SELECTION

# اختيار اليوم
async def select_period(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    period = update.callback_query.data

    if period == "first_ten":
        context.user_data["current_words"] = WORDS_FIRST_TEN
        context.user_data["test_key"] = "first_ten"
    elif period == "middle_ten":
        context.user_data["current_words"] = WORDS_MIDDLE_TEN
        context.user_data["test_key"] = "middle_ten"
    elif period == "last_ten":
        context.user_data["current_words"] = WORDS_LAST_TEN
        context.user_data["test_key"] = "last_ten"

    keyboard = [
        [InlineKeyboardButton(f"اليوم {i+1}", callback_data=f"day_{i}") for i in range(5)],
        [InlineKeyboardButton(f"اليوم {i+6}", callback_data=f"day_{i+5}") for i in range(5)],
    ]
    if period == "last_ten" and len(user_data[user_id]["memorized_words"]) >= 30:
        keyboard.append([InlineKeyboardButton("📝 اختبار العشر الأواخر", callback_data="test_period")])
        keyboard.append([InlineKeyboardButton("📚 اختبار شامل", callback_data="test_all")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_periods")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"🌟 *اختر يومًا من {period.replace('_', ' ')}* 🌟",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return DAY_SELECTION

# عرض الكلمة للحفظ
async def select_day(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    words = context.user_data["current_words"]
    word = words[day_index]

    keyboard = [
        [InlineKeyboardButton("✅ تم الحفظ", callback_data=f"memorize_{day_index}")],
        [InlineKeyboardButton("🔙 رجوع للخلف", callback_data="back_to_days")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
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
        user_data[user_id]["points"] += 10

    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"✅ *تم الحفظ!* نقاطك الآن: {user_data[user_id]['points']}",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return DAY_SELECTION

# اختبار الفترة أو الشامل
async def start_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    test_type = update.callback_query.data

    if test_type == "test_period":
        questions = TEST_QUESTIONS[context.user_data["test_key"]]
    elif test_type == "test_all":
        questions = TEST_QUESTIONS["all_days"]

    question = random.choice(questions)
    context.user_data["current_question"] = question

    await update.callback_query.edit_message_text(
        f"📝 *سؤال الاختبار* 📝\n\n{question['q']}",
    )
    return TEST

# معالجة إجابة الاختبار
async def handle_test_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    question = context.user_data["current_question"]

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_answer.lower() == question["a"].lower():
        await update.message.reply_text(
            "✅ *إجابة صحيحة!*",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "❌ *إجابة خاطئة!*",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    return DAY_SELECTION

# الرجوع للقائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("🕌 مسابقة حفظ الكلمات العلية", callback_data="memorize_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🌙 *اختر من القائمة* 🌙",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MAIN_MENU

# الرجوع لاختيار الفترة
async def back_to_periods(update: Update, context: CallbackContext):
    await memorize_words(update, context)
    return PERIOD_SELECTION

# الرجوع لاختيار اليوم
async def back_to_days(update: Update, context: CallbackContext):
    await select_period(update, context)
    return DAY_SELECTION

# إعداد البوت وتشغيله
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(memorize_words, pattern="^memorize_words$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            PERIOD_SELECTION: [
                CallbackQueryHandler(select_period, pattern="^(first_ten|middle_ten|last_ten)$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            DAY_SELECTION: [
                CallbackQueryHandler(select_day, pattern="^day_"),
                CallbackQueryHandler(start_test, pattern="^(test_period|test_all)$"),
                CallbackQueryHandler(back_to_periods, pattern="^back_to_periods$"),
            ],
            MEMORIZE: [
                CallbackQueryHandler(memorize_word, pattern="^memorize_"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_answer),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
