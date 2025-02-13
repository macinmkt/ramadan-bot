import random
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TOKEN = "YOUR_BOT_TOKEN"

# قائمة الفوائد الرمضانية
ramadan_fawaid = [
    "📜 **راءُ رَمَضَان:** رَحْمَةُ الله للصَّائِمِين، وَالمِيمُ: مَغْفِرَتُهُ لِلمُؤَمِّنِينَ، وَالضَّادُ: ضَمَانُهُ لِجَزَاءِ الصَّائِمِينَ، وَالأَلْفُ: إِحْسَانُهُ للطَائِعين، والنونُ: نُورُه لِلمُحْسِنِينَ.",
    "🌙 **يا بُنَيَّ!** إن رَمَضان نِعْمَة للمسلِمين؛ يَجِيْء بالرحمة والمغفرة والعِتق وقايَة للمؤمنين! فقابِله بالاستقامة، ولا تَتَّبع خُطوات الفاسِدين؛ في الخبر: « إذا جاء رمضان، فُتِحَت أبْوابُ الجَنة » للصالِحين « وغُلِّقَت أبواب النار » عن المُستجيبين « وصُفِّدت الشياطين » دون التائبين.",
    "💡 **فائدة:** الظروف الأرضية هي التي تجعل ليلة القدر متحركة من ليلة لأخرى من ليالي وتر العشر الأخير من رمضان، وأما في السموات فثابتة!"
]

# دالة لإرسال فائدة رمضانية عشوائية
async def send_faidah(update: Update, context: CallbackContext):
    faidah = random.choice(ramadan_fawaid)
    await update.message.reply_text(f"💡 {faidah}")

# إعداد البوت
def main():
    app = Application.builder().token(TOKEN).build()
    
    # أمر لعرض فائدة رمضانية
    app.add_handler(CommandHandler("faidah", send_faidah))

    app.run_polling()

if __name__ == "__main__":
    main()
