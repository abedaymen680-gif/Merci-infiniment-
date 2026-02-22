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

def get_video_duration(file_path):
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
        duration = subprocess.check_output(cmd).decode('utf-8').strip()
        return float(duration)
    except: return 0

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 **قناص المحترفين (سحب + ضغط HEVC)**\n\nالعدادات مفعلة لكل العمليات، أرسل الرابط الآن.")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    url = message.text.strip()
    msg = bot.send_message(MY_ID, "⏱️ كم **ثانية** تريد قنصها ومعالجتها؟")
    bot.register_next_step_handler(msg, lambda m: process_video(m, url))

def process_video(message, url):
    try:
        total_seconds = int(message.text)
        timestamp = int(time.time())
        raw_file = f"raw_{timestamp}.ts"
        final_file = f"pro_{timestamp}.mp4"
        status_msg = bot.send_message(MY_ID, "⏳ جاري تهيئة الاتصال بسيرفرات جوجل...")

        # --- المرحلة الأولى: السحب (Download) مع عداد ---
        cmd_pull = ['ffmpeg', '-y', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        process_pull = subprocess.Popen(cmd_pull, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        last_update = 0
        for line in process_pull.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match and (time.time() - last_update) > 3:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / total_seconds) * 100))
                    bot.edit_message_text(f"📥 **1. جاري سحب البث...**\n{create_progress_bar(percent)} {percent}%\n⏱️ المنجز: {int(current_secs)}/{total_seconds}ث", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_pull.wait()

        # --- المرحلة الثانية: الضغط الاحترافي (HEVC) مع عداد ---
        # نستخدم -c:a copy لضمان عدم لمس جودة الصوت نهائياً
        actual_duration = get_video_duration(raw_file)
        if actual_duration == 0: actual_duration = total_seconds

        bot.edit_message_text(f"⚙️ **2. جاري الضغط الاحترافي (HEVC)...**\nانتظر قليلاً...", MY_ID, status_msg.message_id)
        
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265', '-crf', '28', '-preset', 'faster',
            '-c:a', 'copy', final_file
        ]
        
        process_comp = subprocess.Popen(cmd_comp, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        last_update = 0
        for line in process_comp.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match and (time.time() - last_update) > 3:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / actual_duration) * 100))
                    bot.edit_message_text(f"⚙️ **2. جاري الضغط وتقليل الحجم...**\n{create_progress_bar(percent)} {percent}%\n🔊 الصوت: محفوظ (Original)", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_comp.wait()

        # حسابات الحجم والاستهلاك
        size_mb = os.path.getsize(final_file) / (1024 * 1024)
        consumption_per_hour_gb = (size_mb / actual_duration * 3600) / 1024

        bot.edit_message_text("🚀 جاري الرفع إلى تلجرام...", MY_ID, status_msg.message_id)
        
        with open(final_file, 'rb') as f:
            bot.send_video(MY_ID, f, caption=(
                f"💎 **تم المعالجة باحترافية (HEVC)**\n\n"
                f"📦 الحجم النهائي: {size_mb:.2f} ميجابايت\n"
                f"🔊 جودة الصوت: أصلية 100%\n"
                f"📊 الاستهلاك الساعي المتوقع: {consumption_per_hour_gb:.2f} جيجابايت"
            ))

        # تنظيف الملفات المؤقتة
        for f in [raw_file, final_file]:
            if os.path.exists(f): os.remove(f)

    except Exception as e:
        bot.send_message(MY_ID, f"❌ حدث خطأ: {e}")

print("💀 Professional Sniper is Active...")
bot.polling(none_stop=True)
