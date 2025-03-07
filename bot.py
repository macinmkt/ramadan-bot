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

# قائمة الكلمات لـ 30 يومًا
WORDS = [
    "رمضانُ شهٌر مليٌء بالإحسان!",  # اليوم 1
    "راء رَمَضَان: رَحْمَةُ الله للصَّائِمِين، وَالمِيمُ: مَغْفِرَتُهُ لِلمُؤَمِّنِينَ، وَالضَّادُ: ضَمَانُهُ لِجَزَاءِ الصَّائِمِينَ، وَالأَلْفُ: إِحْسَانُهُ للطَائِعين، والنونُ: نُورُه لِلمُحْسِنِينَ",  # اليوم 2
    # ... (باقى الكلمات كما هى)
]

# الكلمات الكاملة بدون تشكيل للمراجعة
FULL_WORDS = [remove_tashkeel(word) for word in WORDS]

# دالة لإزالة التشكيل من النصوص
def remove_tashkeel(text):
    tashkeel = (
        '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650', '\u0651', '\u0652',
        '\u0653', '\u0654', '\u0655', '\u0656', '\u0657', '\u0658', '\u0659', '\u065A',
        '\u065B', '\u065C', '\u065D', '\u065E', '\u065F', '\u0670'
    )
    return text.translate(str.maketrans('', '', ''.join(tashkeel)))

# حفظ بيانات المستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": []}

    context.user_data["current_words"] = WORDS
    await show_days(update, context)
    return DAY_SELECTION

async def show_days(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id
    words = context.user_data["current_words"]

    # إنشاء لوحة المفاتيح مع التحقق من الحالة
    keyboard = []
    for i in range(0, 30, 3):
        row = []
        for j in range(i, min(i+3, 30)):
            status = ' ✅' if words[j] in user_data[user_id]["memorized_words"] else ''
            row.append(InlineKeyboardButton(f"اليوم {j+1}{status}", callback_data=f"day_{j}"))
        keyboard.append(row)

    # إضافة أزرار المراجعة والاختبار إذا لزم الأمر
    if user_data[user_id]["memorized_words"]:
        keyboard.extend([
            [InlineKeyboardButton("📖 مراجعة", callback_data="review")],
            [InlineKeyboardButton("📚 اختبار شامل", callback_data="test_all")]
        ])

    message = (
        "🌙 *رحلة حفظ الكلمات العلية في شهر رمضان المبارك* 🌙\n\n"
        "✨ انطلق في مغامرة يومية مع كلمات الحكمة والمعرفة في شهر الخير\n"
        "📅 اختر اليوم واحفظ الكلمة ثم اضغط *تم الحفظ* 🌟\n"
        "📖 استمتع بمراجعة كنوزك المحفوظة عبر زر *مراجعة* ✨\n"
        "📝 أو تحدَّ نفسك باختبار شامل من خلال زر *اختبار شامل* 🏆"
    )

    try:
        if query:
            # التحقق من أن المحتوى تغير قبل التعديل
            current_text = query.message.text
            current_markup = query.message.reply_markup
            new_markup = InlineKeyboardMarkup(keyboard)
            
            if current_text != message or str(current_markup) != str(new_markup):
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        if "Message is not modified" not in str(e):
            raise e

    return DAY_SELECTION

# معالجة اختيار اليوم
async def select_day(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day_index = int(query.data.split("_")[1])
    word = context.user_data["current_words"][day_index]

    keyboard = [
        [InlineKeyboardButton("✅ تم الحفظ", callback_data=f"memorize_{day_index}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]
    ] if word not in user_data[user_id]["memorized_words"] else [
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]
    ]

    await query.edit_message_text(
        f"📜 *اليوم {day_index + 1}*\n\n{word}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MEMORIZE

# معالجة الحفظ
async def memorize_word(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day_index = int(query.data.split("_")[1])
    word = context.user_data["current_words"][day_index]

    if word not in user_data[user_id]["memorized_words"]:
        user_data[user_id]["memorized_words"].append(word)

    await query.edit_message_text("✅ *تم الحفظ بنجاح!*", parse_mode="Markdown")
    await show_days(update, context)
    return DAY_SELECTION

# مراجعة الكلمات المحفوظة
async def review(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await query.edit_message_text(
            "📖 *لم تضف كلمات إلى كنزك بعد!*",
            parse_mode="Markdown"
        )
    else:
        review_text = "📖 *كنوزك المحفوظة:*\n\n" + "\n".join(memorized)
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]]
        await query.edit_message_text(
            review_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return DAY_SELECTION

# اختبار شامل
async def start_test(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await query.edit_message_text(
            "📚 *لا كلمات محفوظة لاختبارها بعد!*",
            parse_mode="Markdown"
        )
        return DAY_SELECTION

    context.user_data["test_words"] = memorized
    context.user_data["last_question"] = None
    await ask_next_question(update, context)
    return TEST

async def ask_next_question(update: Update, context: CallbackContext):
    words = context.user_data["test_words"]
    word_phrase = random.choice(words)
    word_parts = word_phrase.split()

    if len(word_parts) < 2:
        question = word_phrase
        correct_answer = word_phrase
    else:
        blank_pos = random.randint(0, len(word_parts)-1)
        correct_answer = word_parts[blank_pos]
        word_parts[blank_pos] = "ـــــــ"
        question = " ".join(word_parts)

    context.user_data["current_question"] = {"q": question, "a": correct_answer}

    await (update.callback_query.edit_message_text if update.callback_query else update.message.reply_text)(
        f"📝 *املأ الفراغ:*\n\n{question}",
        parse_mode="Markdown"
    )

async def handle_test_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text.strip()
    question = context.user_data["current_question"]

    user_clean = remove_tashkeel(user_answer).lower()
    correct_clean = remove_tashkeel(question["a"]).lower()

    result = (
        "✅ *إجابة صحيحة!*\n\n" + f"الإجابة: {question['a']}"
        if user_clean == correct_clean
        else f"❌ *إجابة خاطئة!* الإجابة الصحيحة: {question['a']}"
    )

    keyboard = [
        [InlineKeyboardButton("➡️ سؤال آخر", callback_data="next_question")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]
    ]
    
    await update.message.reply_text(
        result,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return TEST

# الرجوع لاختيار اليوم
async def back_to_days(update: Update, context: CallbackContext):
    await update.callback_query.answer()
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
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$")
            ],
            MEMORIZE: [
                CallbackQueryHandler(memorize_word, pattern="^memorize_"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$")
            ],
            TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_answer),
                CallbackQueryHandler(ask_next_question, pattern="^next_question$"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
