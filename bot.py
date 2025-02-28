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
            "🌙
