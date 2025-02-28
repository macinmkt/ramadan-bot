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
PERIOD_SELECTION, DAY_SELECTION, MEMORIZE, TEST = range(4)

# قوائم الكلمات لكل فترة
WORDS_FIRST_TEN = [
    "الصبر مفتاح الفرج", "الصوم جنة", "القرآن هدى", "الصدقة تطفئ الغضب", "الصلاة نور",
    "الذكر راحة", "التوبة مغفرة", "الدعاء عبادة", "الإخلاص سر النجاح", "رمضان فرصة",
]

WORDS_MIDDLE_TEN = [
    "التقوى زاد", "الصمت حكمة", "القلب مرآة", "الجار حق", "الأمل قوة",
    "الرضا كنز", "العمل صلاح", "الشكر نعمة", "العدل أساس", "التوكل يقين",
]

WORDS_LAST_TEN = [
    "ليلة القدر خير", "العتق من النار", "الاجتهاد فضيلة", "التهجد قربة", "الاستغفار مفتاح",
    "القيام بركة", "الإنفاق ثواب", "الخشوع راحة", "العيد فرحة", "رم
