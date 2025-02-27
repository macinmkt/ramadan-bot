import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

# القوائم الرئيسية
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("📚 فوائد متنوعة"))
    markup.add(KeyboardButton("📝 برنامج حفظ الكلمات العلي"))
    return markup

# قائمة برنامج حفظ الكلمات العلي
def word_saving_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("القسم الأول"))
    markup.add(KeyboardButton("القسم الثاني"))
    markup.add(KeyboardButton("القسم الثالث"))
    markup.add(KeyboardButton("🔙 الرجوع"))
    return markup

# قائمة خيارات القسم
def section_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("📖 عرض الكلمات"))
    markup.add(KeyboardButton("📝 اختبار حفظك"))
    markup.add(KeyboardButton("🔙 الرجوع"))
    return markup

# قائمة عرض الكلمات
def word_display_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    for i in range(1, 11):
        markup.add(KeyboardButton(str(i)))
    markup.add(KeyboardButton("🔙 الرجوع"))
    return markup

# قائمة الاختبار
def test_result_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(KeyboardButton("✔️ تم الحفظ"))
    markup.add(KeyboardButton("🔄 احتاج مراجعتها"))
    markup.add(KeyboardButton("🔙 الرجوع"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك! اختر من القائمة الرئيسية:", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "📚 فوائد متنوعة")
def send_benefits(message):
    bot.send_message(message.chat.id, "📌 فائدة اليوم: [نص فائدة متنوعة هنا]")

@bot.message_handler(func=lambda message: message.text == "📝 برنامج حفظ الكلمات العلي")
def send_word_saving(message):
    bot.send_message(message.chat.id, "اختر القسم الذي ترغب في حفظه:", reply_markup=word_saving_menu())

@bot.message_handler(func=lambda message: message.text in ["القسم الأول", "القسم الثاني", "القسم الثالث"])
def section_options(message):
    bot.send_message(message.chat.id, f"اختر ما تود القيام به في {message.text}:", reply_markup=section_menu())

@bot.message_handler(func=lambda message: message.text == "📖 عرض الكلمات")
def show_words(message):
    bot.send_message(message.chat.id, "اختر رقم الكلمة التي تريد عرضها:", reply_markup=word_display_menu())

@bot.message_handler(func=lambda message: message.text.isdigit() and 1 <= int(message.text) <= 10)
def display_word(message):
    bot.send_message(message.chat.id, f"الكلمة رقم {message.text}: [الكلمة هنا]", reply_markup=test_result_menu())

@bot.message_handler(func=lambda message: message.text in ["✔️ تم الحفظ", "🔄 احتاج مراجعتها", "🔙 الرجوع"])
def return_to_main(message):
    bot.send_message(message.chat.id, "تم الرجوع للقائمة الرئيسية", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "📝 اختبار حفظك")
def start_test(message):
    bot.send_message(message.chat.id, "سيتم اختبارك في الكلمات، أجب عن الأسئلة التالية:")
    # يمكن تطوير الاختبار ليكون تفاعليًا مع حساب النقاط

bot.polling(none_stop=True)
