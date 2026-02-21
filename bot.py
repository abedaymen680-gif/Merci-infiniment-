import os, subprocess, telebot, time, re

# إعدادات البوت
TOKEN = "8589322439:AAE7PESv8wSmSp5sOsVIfo60Uzs8KhrKkXw"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🛡️ نظام القناص (إصدار Temp.sh):\n✅ الصيغة: MPEG-TS\n✅ الضغط: HEVC\nأرسل الرابط الآن.")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    url = message.text
    if "http" in url:
        msg = bot.send_message(MY_ID, "⏱️ كم دقيقة تريد التسجيل؟")
        bot.register_next_step_handler(msg, lambda m: process_video(m, url))

def process_video(message, url):
    try:
        minutes = float(message.text)
        total_seconds = int(minutes * 60)
        
        # ملفات مؤقتة بأسماء فريدة لتجنب التداخل
        timestamp = int(time.time())
        raw_file = f"raw_{timestamp}.ts"
        final_file = f"video_{timestamp}.ts"
        
        status = bot.send_message(MY_ID, "📥 **جاري سحب البث...**")

        # 1. سحب البث
        subprocess.run(['ffmpeg', '-y', '-reconnect', '1', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file])

        # 2. الضغط بنظام HEVC (H.265) داخل حاوية TS
        bot.edit_message_text("⚙️ **جاري الضغط (HEVC)...**", MY_ID, status.message_id)
        
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265', '-crf', '28', '-preset', 'ultrafast',
            '-c:a', 'aac', '-f', 'mpegts', 
            final_file
        ]
        subprocess.run(cmd_comp)

        # 3. الرفع على Temp.sh
        size = os.path.getsize(final_file) / (1024*1024)
        bot.edit_message_text(f"🚀 اكتمل الضغط ({size:.2f} MB). جاري الرفع على Temp.sh...", MY_ID, status.message_id)
        
        try:
            # استخدام curl للرفع على temp.sh
            upload_cmd = f"curl -F 'file=@{final_file}' https://temp.sh/upload"
            link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()
        except:
            link = None

        if link and "http" in link:
            # تنبيه المستخدم أن الملف TS لسهولة التحميل الجزئي
            bot.send_message(MY_ID, f"✅ **تم القنص بنجاح!**\n\n🔗 رابط Temp.sh:\n{link}\n\n💡 ملاحظة: الملف بصيغة .ts ليعمل معك في ترمكس حتى لو حملت 5 ميجا فقط.")
        else:
            bot.send_message(MY_ID, "⚠️ فشل الرفع، جاري إرسال الملف مباشرة...")
            with open(final_file, 'rb') as f:
                bot.send_document(MY_ID, f)
            
        # تنظيف
        for f in [raw_file, final_file]:
            if os.path.exists(f): os.remove(f)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
