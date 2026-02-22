import os, subprocess, telebot, time, re

# إعدادات البوت
TOKEN = "8589322439:AAE-YJwCtvcfnk9APtSu6RZl9127Rcr7YC4"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

def create_progress_bar(percent):
    bar_length = 10
    filled_length = int(bar_length * percent / 100)
    bar = "▓" * filled_length + "░" * (bar_length - filled_length)
    return bar

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 **قناص جوجل كولاب الجاهز (بدون ضغط)**\n\nأرسل الرابط وسأحسب لك معدل الاستهلاك الساعي.")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    url = message.text.strip()
    msg = bot.send_message(MY_ID, "⏱️ كم **ثانية** تريد قنصها لاختبار الاستهلاك؟")
    bot.register_next_step_handler(msg, lambda m: process_video(m, url))

def process_video(message, url):
    try:
        total_seconds = int(message.text)
        timestamp = int(time.time())
        # سنستخدم امتداد .mp4 أو .ts حسب المصدر بدون إعادة ترميز
        raw_file = f"sniper_{timestamp}.mp4"
        status_msg = bot.send_message(MY_ID, "⏳ جاري بدء السحب المباشر...")

        # --- عملية السحب فقط (Copy) بدون ضغط ---
        cmd_pull = ['ffmpeg', '-y', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        process_pull = subprocess.Popen(cmd_pull, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        last_update = 0
        for line in process_pull.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match and (time.time() - last_update) > 5:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / total_seconds) * 100))
                    bot.edit_message_text(f"📥 **جاري السحب من المصدر...**\n{create_progress_bar(percent)} {percent}%\n⏱️ المنجز: {int(current_secs)}/{total_seconds}ث", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_pull.wait()

        # حساب الحجم والبيانات الساعية
        file_size_bytes = os.path.getsize(raw_file)
        size_mb = file_size_bytes / (1024 * 1024)
        
        # الحساب الساعي: (الحجم الحالي / الثواني المقنوصة) * 3600 ثانية
        consumption_per_hour_gb = (size_mb / total_seconds * 3600) / 1024

        bot.edit_message_text("🚀 جاري إرسال العينة المقنوصة...", MY_ID, status_msg.message_id)
        
        with open(raw_file, 'rb') as f:
            bot.send_video(MY_ID, f, caption=(
                f"✅ **تقرير قنص البيانات**\n\n"
                f"📦 حجم العينة: {size_mb:.2f} ميجابايت\n"
                f"⏱️ مدة العينة: {total_seconds} ثانية\n"
                f"📊 **الاستهلاك المتوقع في الساعة:**\n"
                f"⬅️ {consumption_per_hour_gb:.2f} جيجابايت/ساعة\n\n"
                f"⚠️ ملاحظة: التحميل بدون ضغط للحفاظ على الجودة الأصلية."
            ))

        # تنظيف
        if os.path.exists(raw_file): os.remove(raw_file)

    except Exception as e:
        bot.send_message(MY_ID, f"❌ حدث خطأ: {e}")

print("🚀 Sniper Raw Bot is Active...")
bot.polling(none_stop=True)
