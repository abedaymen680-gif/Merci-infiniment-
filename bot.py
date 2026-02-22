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

def upload_to_temp(file_path):
    try:
        # الرفع إلى temp.sh والحصول على الرابط المباشر
        cmd = f"curl -T {file_path} https://temp.sh/{os.path.basename(file_path)}"
        link = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        return link
    except:
        return "❌ فشل الرفع إلى Temp.sh"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 **قناص المحترفين (HEVC + Temp.sh)**\n\nصوت أصلي، حجم مثالي، ورابط مباشر.")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    url = message.text.strip()
    msg = bot.send_message(MY_ID, "⏱️ كم **ثانية** تريد قنصها؟")
    bot.register_next_step_handler(msg, lambda m: process_video(m, url))

def process_video(message, url):
    try:
        total_seconds = int(message.text)
        timestamp = int(time.time())
        raw_file = f"raw_{timestamp}.ts"
        final_file = f"hevc_{timestamp}.mp4"
        status_msg = bot.send_message(MY_ID, "⏳ جاري بدء العملية...")

        # --- 1. سحب البث الخام ---
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
                    bot.edit_message_text(f"📥 **1. جاري سحب الخام...**\n{create_progress_bar(percent)} {percent}%", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_pull.wait()

        # --- 2. الضغط الاحترافي (HEVC) ---
        actual_duration = get_video_duration(raw_file)
        if actual_duration == 0: actual_duration = total_seconds
        
        bot.edit_message_text("⚙️ **2. جاري الضغط الاحترافي (HEVC)...**", MY_ID, status_msg.message_id)
        
        # استخدمنا -crf 30 لتقليل الحجم أكثر مع بقاء الجودة ممتازة
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265', '-crf', '30', '-preset', 'faster',
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
                    bot.edit_message_text(f"⚙️ **2. جاري الضغط (HEVC)...**\n{create_progress_bar(percent)} {percent}%\n🔊 الصوت: أصلي", MY_ID, status_msg.message_id)
                    last_update = time.time()
        process_comp.wait()

        # --- 3. الرفع والحسابات ---
        size_mb = os.path.getsize(final_file) / (1024 * 1024)
        consumption_per_hour_gb = (size_mb / actual_duration * 3600) / 1024

        bot.edit_message_text("☁️ جاري الرفع إلى Temp.sh وتجهيز التلجرام...", MY_ID, status_msg.message_id)
        
        temp_link = upload_to_temp(raw_file) # نرفع الملف الخام للرابط لأعلى جودة

        with open(final_file, 'rb') as f:
            bot.send_video(MY_ID, f, caption=(
                f"💎 **تم القنص والضغط بنجاح**\n\n"
                f"📦 الحجم: {size_mb:.2f} ميجابايت\n"
                f"📊 الاستهلاك الساعي: {consumption_per_hour_gb:.2f} جيجابايت\n\n"
                f"🔗 رابط الملف الخام (Direct): \n{temp_link}"
            ))

        for f in [raw_file, final_file]:
            if os.path.exists(f): os.remove(f)

    except Exception as e:
        bot.send_message(MY_ID, f"❌ حدث خطأ: {e}")

print("💀 Pro Sniper is running...")
bot.polling(none_stop=True)
