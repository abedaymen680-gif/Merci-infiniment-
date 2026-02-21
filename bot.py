import os, subprocess, telebot, time, re

# التوكن الخاص بك
TOKEN = "8589322439:AAHRuYzx9VnXsjZ_ju1l_16XUbLhkWkQ5K8"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 بوت القناص (النسخة الذكية):\n✅ تم ضبط الضغط لتقليل الحجم (CRF 33)\n✅ عدادات لحظية للسحب والضغط\n✅ رفع تلقائي إذا تجاوز الملف 50MB")

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
        raw_file = "raw_video.ts"
        final_file = "final_video.mp4"
        
        status_msg = bot.send_message(MY_ID, "📥 **المرحلة 1: جاري سحب البث...**")

        # 1. سحب البث مع إعادة اتصال تلقائية
        cmd_pull = [
            'ffmpeg', '-y', 
            '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_at_eof', '1', 
            '-i', url, '-t', str(total_seconds), 
            '-c', 'copy', raw_file
        ]
        proc_pull = subprocess.Popen(cmd_pull, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        last_update = 0
        for line in proc_pull.stdout:
            match = re.search(r"time=(\d+):(\d+):(\d+)", line)
            if match and (time.time() - last_update >= 10):
                h, m, s = map(int, match.groups())
                curr = h*3600 + m*60 + s
                p = min(int((curr/total_seconds)*100), 100)
                try: bot.edit_message_text(f"📥 **جاري السحب:**\n✅ المنجز: {curr}/{total_seconds} ثانية ({p}%)", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_pull.wait()

        # 2. الضغط الذكي (تقليل الحجم)
        bot.edit_message_text("⚙️ **المرحلة 2: جاري الضغط وتقليل الحجم...**", MY_ID, status_msg.message_id)
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file, 
            '-c:v', 'libx264', 
            '-crf', '33',               # سر الحجم الصغير جداً
            '-preset', 'veryfast',       # توازن ذكي بين الوقت والمساحة
            '-c:a', 'aac', 
            '-b:a', '128k', 
            '-movflags', 'faststart', 
            final_file
        ]
        proc_comp = subprocess.Popen(cmd_comp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        last_update = 0
        for line in proc_comp.stdout:
            match = re.search(r"time=(\d+):(\d+):(\d+)", line)
            if match and (time.time() - last_update >= 10):
                h, m, s = map(int, match.groups())
                curr = h*3600 + m*60 + s
                p = min(int((curr/total_seconds)*100), 100)
                try: bot.edit_message_text(f"⚙️ **جاري الضغط:**\n✅ المنجز: {curr}/{total_seconds} ثانية ({p}%)", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_comp.wait()

        # 3. التحقق من الحجم والإرسال
        size = os.path.getsize(final_file) / (1024*1024)
        if size > 48:
            bot.send_message(MY_ID, f"📦 الحجم: {size:.2f} MB (أكبر من حدود تلجرام)\n🚀 جاري الرفع إلى BashUpload...")
            upload_cmd = f"curl -T {final_file} https://bashupload.com/{final_file}"
            upload_result = subprocess.check_output(upload_cmd, shell=True).decode('utf-8')
            links = re.findall(r'https://bashupload.com/[^\s]+', upload_result)
            if links:
                bot.send_message(MY_ID, f"✅ تم الرفع بنجاح!\n🔗 رابط التحميل المباشر:\n{links[0]}")
            else:
                bot.send_message(MY_ID, "⚠️ فشل الرفع، أحاول إرساله كملف...")
                with open(final_file, 'rb') as f: bot.send_video(MY_ID, f)
        else:
            bot.send_message(MY_ID, f"✅ اكتملت المهمة! الحجم: {size:.2f} MB")
            with open(final_file, 'rb') as f: bot.send_video(MY_ID, f)
            
        # تنظيف المساحة
        if os.path.exists(raw_file): os.remove(raw_file)
        if os.path.exists(final_file): os.remove(final_file)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
                
