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
    except:
        return 0

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 نظام القناص المزدوج جاهز.\nالعداد مفعل للتحميل والضغط.\nأرسل الرابط الآن.")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    url = message.text.strip()
    msg = bot.send_message(MY_ID, "⏱️ كم ثانية تريد التسجيل؟")
    bot.register_next_step_handler(msg, lambda m: process_video(m, url))

def process_video(message, url):
    try:
        total_seconds = int(message.text)
        timestamp = int(time.time())
        raw_file = f"raw_{timestamp}.ts"
        final_file = f"final_{timestamp}.ts"
        status_msg = bot.send_message(MY_ID, "⏳ بدء العمل...")

        # 1. عداد مرحلة التحميل (Pulling)
        cmd_pull = ['ffmpeg', '-y', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        process_pull = subprocess.Popen(cmd_pull, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        last_update = 0
        for line in process_pull.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match and (time.time() - last_update) > 4:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / total_seconds) * 100))
                    bot.edit_message_text(f"📥 **1. جاري التحميل...**\n{create_progress_bar(percent)} {percent}%\n⏱️ المنجز: {int(current_secs)}/{total_seconds} ثانية", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_pull.wait()

        # 2. عداد مرحلة الضغط (Compression)
        actual_duration = get_video_duration(raw_file)
        if actual_duration == 0: actual_duration = total_seconds # احتياطي

        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265', '-crf', '30', '-preset', 'ultrafast',
            '-c:a', 'aac', '-b:a', '32k', final_file
        ]
        
        process_comp = subprocess.Popen(cmd_comp, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        bot.edit_message_text(f"⚙️ **2. جاري الضغط (HEVC)...**\nانتظر قليلاً", MY_ID, status_msg.message_id)
        
        last_update = 0
        for line in process_comp.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match and (time.time() - last_update) > 4:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / actual_duration) * 100))
                    bot.edit_message_text(f"⚙️ **2. جاري الضغط (HEVC)...**\n{create_progress_bar(percent)} {percent}%\n⏱️ المنجز: {int(current_secs)}/{int(actual_duration)} ثانية", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_comp.wait()

        # 3. حساب الحجم والرفع
        size_mb = os.path.getsize(final_file) / (1024 * 1024)
        bot.edit_message_text("🚀 جاري الرفع النهائي...", MY_ID, status_msg.message_id)
        
        upload_cmd = f"curl -F 'file=@{final_file}' https://temp.sh/upload"
        link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()

        report = (
            f"✅ **اكتمل القنص بنجاح**\n\n"
            f"📦 الحجم: {size_mb:.2f} MB\n"
            f"⏱️ المنجز فعلياً: {int(actual_duration)} ثانية\n"
            f"🔗 الرابط:\n{link}"
        )
        bot.send_message(MY_ID, report)

        for f in [raw_file, final_file]:
            if os.path.exists(f): os.remove(f)

    except Exception as e:
        bot.send_message(MY_ID, f"❌ حدث خطأ: {e}")

bot.polling(none_stop=True)
