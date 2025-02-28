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
from datetime import time, datetime, timedelta

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

# حالات المحادثة
MAIN_MENU, WORD_COUNT, REVIEW_WORDS, COMPLETE_GAP = range(4)

# قائمة الكلمات
WORDS = [
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
]

# قائمة الجمل الناقصة
GAP_SENTENCES = [
    {"sentence": "هذا النص هو مثال لنص يمكن أن ______ في نفس المساحة.", "answer": "يستبدل"},
    {"sentence": "لقد تم توليد هذا النص من مولد النص العربى، ______.", "answer": "حيث"},
]

# قائمة الفوائد المتنوعة عن رمضان
BENEFITS = [
    "🌙 الصوم في رمضان يعلم الصبر والتحمل ويقوي الإرادة.",
    "🌟 رمضان فرصة للتوبة والرجوع إلى الله بقلب سليم.",
    "🕌 قيام الليل في رمضان من أفضل العبادات التي تقرب العبد إلى ربه.",
    "📿 الصدقة في رمضان تتضاعف أجرها، فهي مغنم عظيم.",
    "🌼 رمضان شهر القرآن، ففيه أنزل القرآن الكريم هدى للناس.",
    "⏰ الصيام يذكرنا بنعمة الطعام والشراب التي نغفل عنها.",
    "🌌 ليلة القدر في رمضان خير من ألف شهر، فاغتنمها.",
]

# حفظ الكلمات التي تم إرسالها للمستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": [], "points": 0, "sent_benefits": []}  # تهيئة بيانات المستخدم مع قائمة الفوائد المرسلة

    # رسالة ترحيبية
    welcome_message = (
        "🌙 *رمضان كريم* 🌙\n\n"
        "مرحبًا بك في بوت رمضان! هنا يمكنك:\n"
        "- الحصول على فوائد متنوعة.\n"
        "- حفظ الكلمات العلية.\n"
        "- اختبار حفظك باستخدام 'اكمل الفراغ'.\n\n"
        "اختر من القائمة أدناه:"
    )

    keyboard = [
        [InlineKeyboardButton("🌙 فوائد متنوعة", callback_data="daily_faidah")],
        [InlineKeyboardButton("🕌 اشترك في برنامج حفظ الكلمات العلية", callback_data="memorize_words")],
        [InlineKeyboardButton("📝 اختبار حفظك (اكمل الفراغ)", callback_data="complete_gap")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
    return MAIN_MENU

# معالجة اختيار فوائد متنوعة
async def daily_faidah(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # تهيئة قائمة الفوائد المرسلة إذا لم تكن موجودة
    if "sent_benefits" not in user_data[user_id]:
        user_data[user_id]["sent_benefits"] = []

    # تصفية الفوائد غير المرسلة
    available_benefits = [b for b in BENEFITS if b not in user_data[user_id]["sent_benefits"]]

    if available_benefits:
        # اختيار فائدة عشوائية من الفوائد المتاحة
        selected_benefit = random.choice(available_benefits)
        user_data[user_id]["sent_benefits"].append(selected_benefit)
        message = f"🌟 *فائدة جديدة* 🌟\n\n{selected_benefit}"
    else:
        message = "🌙 *تم استلام كل الفوائد!* 🌙\n\nلقد استلمت جميع الفوائد المتاحة حاليًا، عد لاحقًا للمزيد!"

    keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MAIN_MENU

# معالجة اختيار برنامج حفظ الكلمات العلية
async def memorize_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # إذا كان المستخدم قد حفظ كلمات من قبل، نعرض خيار "مراجعة الكلمات"
    if user_data[user_id]["memorized_words"]:
        keyboard = [
            [InlineKeyboardButton("📖 مراجعة الكلمات", callback_data="review_words")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "لقد قمت بحفظ كلمات من قبل. اختر مراجعة الكلمات:",
            reply_markup=reply_markup,
        )
        return REVIEW_WORDS
    else:
        # إذا لم يحفظ كلمات من قبل، نعرض خيار "كلمة واحدة" أو "كلمتين"
        keyboard = [
            [InlineKeyboardButton("📜 كلمة واحدة", callback_data="one_word")],
            [InlineKeyboardButton("📜 كلمتين", callback_data="two_words")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "🌙 *كم عدد الكلمات التي تريد حفظها؟* 🌙",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        return WORD_COUNT

# معالجة اختيار عدد الكلمات
async def word_count(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    choice = update.callback_query.data

    if choice == "one_word":
        words_to_send = WORDS[:1]  # إرسال كلمة واحدة
    else:
        words_to_send = WORDS[:2]  # إرسال كلمتين

    # حفظ الكلمات التي تم إرسالها
    if "memorized_words" not in user_data[user_id]:
        user_data[user_id]["memorized_words"] = []
    user_data[user_id]["memorized_words"].extend(words_to_send)

    # إرسال الكلمات مع زر تأكيد الحفظ
    words_text = "\n\n".join(words_to_send)
    keyboard = [
        [InlineKeyboardButton("✅ تم الحفظ", callback_data="confirm_memorized")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"🌟 *الكلمات التي تم إرسالها* 🌟\n\n{words_text}",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MAIN_MENU

# معالجة مراجعة الكلمات
async def review_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # جلب الكلمات المحفوظة
    memorized_words = user_data[user_id]["memorized_words"]
    if memorized_words:
        # تنسيق الكلمات بشكل جديد
        words_text = "📖 *الكلمات العلية* 📖\n\n"
        for i, word in enumerate(memorized_words, start=1):
            words_text += f"الكلمة {i}: {word}\n\n"

        keyboard = [
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            words_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.callback_query.edit_message_text("لم تقم بحفظ أي كلمات حتى الآن.")

    return MAIN_MENU

# معالجة اختيار اختبار "اكمل الفراغ"
async def complete_gap(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # اختيار جملة ناقصة عشوائية
    gap_sentence = random.choice(GAP_SENTENCES)
    context.user_data["current_gap"] = gap_sentence

    await update.callback_query.edit_message_text(
        f"📝 *اكمل الفراغ* 📝\n\n{gap_sentence['sentence']}"
    )
    return COMPLETE_GAP

# معالجة إجابة المستخدم على "اكمل الفراغ"
async def handle_gap_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    gap_sentence = context.user_data.get("current_gap")

    if gap_sentence and user_answer.lower() == gap_sentence["answer"].lower():
        # إضافة نقاط للمستخدم
        if "points" not in user_data[user_id]:
            user_data[user_id]["points"] = 0
        user_data[user_id]["points"] += 10
        await update.message.reply_text(f"✅ إجابة صحيحة! نقاطك الآن: {user_data[user_id]['points']}")
    else:
        await update.message.reply_text("❌ إجابة خاطئة، حاول مرة أخرى!")

    return MAIN_MENU

# الرجوع للقائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("🌙 فوائد متنوعة", callback_data="daily_faidah")],
        [InlineKeyboardButton("🕌 اشترك في برنامج حفظ الكلمات العلية", callback_data="memorize_words")],
        [InlineKeyboardButton("📝 اختبار حفظك (اكمل الفراغ)", callback_data="complete_gap")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🌙 *اختر من القائمة* 🌙",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MAIN_MENU

# إعداد البوت وتشغيله
def main():
    # استخدام ApplicationBuilder لإنشاء Application مع JobQueue
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(daily_faidah, pattern="^daily_faidah$"),
                CallbackQueryHandler(memorize_words, pattern="^memorize_words$"),
                CallbackQueryHandler(complete_gap, pattern="^complete_gap$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            WORD_COUNT: [
                CallbackQueryHandler(word_count, pattern="^one_word$"),
                CallbackQueryHandler(word_count, pattern="^two_words$"),
            ],
            REVIEW_WORDS: [
                CallbackQueryHandler(review_words, pattern="^review_words$"),
            ],
            COMPLETE_GAP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gap_answer),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
