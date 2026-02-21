import os, subprocess, telebot, time, re

# إعدادات البوت
TOKEN = "8589322439:AAGfZp8M70CZ7HM6O8nI6RPPRvnqTarvy38"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    welcome_msg = (
        "🛡️ تم تشغيل نظام القناص الاحترافي\n"
        "━━━━━━━━━━━━━\n"
        "✅ ترميز HEVC (H.265) نشط\n"
        "✅ عداد السحب والضغط مفعل\n"
        "✅ الرفع المباشر: Temp.sh\n"
        "━━━━━━━━━━━━━\n"
        "أرسل رابط البث الآن."
    )
    bot.send_message(MY_ID, welcome_msg)

def create_progress_bar(percent):
    """صناعة شكل شريط التحميل"""
    bar_length = 10
    filled_length = int(bar_length * percent / 100)
    bar = "▓" * filled_length + "░" * (bar_length - filled_length)
    return bar

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
        timestamp = int(time.time())
        raw_file = f"raw_{timestamp}.ts"
        final_file = f"video_{timestamp}.ts"
        
        status_msg = bot.send_message(MY_ID, "📥 **بدء سحب البث...**")

        # 1. سحب البث مع عداد (بناءً على الوقت)
        cmd_pull = ['ffmpeg', '-y', '-reconnect', '1', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        process_pull = subprocess.Popen(cmd_pull, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        last_update = 0
        for line in process_pull.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / total_seconds) * 100))
                    if time.time() - last_update > 5:
                        bot.edit_message_text(f"📥 **جاري سحب البث...**\n\n{create_progress_bar(percent)} {percent}%", MY_ID, status_msg.message_id)
                        last_update = time.time()
        process_pull.wait()

        # 2. الضغط مع عداد النسبة المئوية
        bot.edit_message_text("⚙️ **جاري معالجة وضغط الفيديو...**", MY_ID, status_msg.message_id)
        
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265', '-crf', '28', '-preset', 'ultrafast',
            '-c:a', 'aac', '-f', 'mpegts', final_file
        ]
        
        process_comp = subprocess.Popen(cmd_comp, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
        
        last_update = 0
        for line in process_comp.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
                if time_match:
                    h, m, s = map(float, time_match.group(1).split(':'))
                    current_secs = h * 3600 + m * 60 + s
                    percent = min(100, int((current_secs / total_seconds) * 100))
                    if time.time() - last_update > 5:
                        bot.edit_message_text(f"⚙️ **جاري الضغط (HEVC)...**\n\n{create_progress_bar(percent)} {percent}%", MY_ID, status_msg.message_id)
                        last_update = time.time()
        process_comp.wait()

        # 3. الرفع
        bot.edit_message_text("🚀 **اكتملت المعالجة! جاري الرفع الآن...**", MY_ID, status_msg.message_id)
        upload_cmd = f"curl -F 'file=@{final_file}' https://temp.sh/upload"
        link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()

        if link:
            bot.send_message(MY_ID, f"✅ **تم القنص بنجاح!**\n\n🔗 الرابط:\n{link}")
        else:
            bot.send_document(MY_ID, open(final_file, 'rb'))
            
        # تنظيف
        for f in [raw_file, final_file]:
            if os.path.exists(f): os.remove(f)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
        
