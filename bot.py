import os, subprocess, telebot, time, re

# التوكن الجديد الذي أرسلته
TOKEN = "8589322439:AAHRuYzx9VnXsjZ_ju1l_16XUbLhkWkQ5K8"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "✅ تم التحديث بالتوكن الجديد!\nنظام GitHub Actions جاهز الآن مع العدادات (سحب + ضغط).")

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

        # سحب البث مع عداد
        cmd_pull = ['ffmpeg', '-y', '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_at_eof', '1', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        proc_pull = subprocess.Popen(cmd_pull, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        last_update = 0
        for line in proc_pull.stdout:
            match = re.search(r"time=(\d+):(\d+):(\d+)", line)
            if match and (time.time() - last_update >= 8):
                h, m, s = map(int, match.groups())
                curr = h*3600 + m*60 + s
                p = min(int((curr/total_seconds)*100), 100)
                try: bot.edit_message_text(f"📥 **جاري السحب:**\n✅ المنجز: {curr}/{total_seconds} ثانية ({p}%)", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_pull.wait()

        # الضغط مع عداد
        bot.edit_message_text("⚙️ **المرحلة 2: جاري الضغط (HEVC)...**", MY_ID, status_msg.message_id)
        cmd_comp = ['ffmpeg', '-y', '-i', raw_file, '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', '-c:a', 'aac', '-movflags', 'faststart', final_file]
        proc_comp = subprocess.Popen(cmd_comp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        last_update = 0
        for line in proc_comp.stdout:
            match = re.search(r"time=(\d+):(\d+):(\d+)", line)
            if match and (time.time() - last_update >= 8):
                h, m, s = map(int, match.groups())
                curr = h*3600 + m*60 + s
                p = min(int((curr/total_seconds)*100), 100)
                try: bot.edit_message_text(f"⚙️ **جاري الضغط:**\n✅ المنجز: {curr}/{total_seconds} ثانية ({p}%)", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_comp.wait()

        size = os.path.getsize(final_file) / (1024*1024)
        bot.send_message(MY_ID, f"✅ اكتملت المهمة بنجاح!\n📦 الحجم النهائي: {size:.2f} MB")
        with open(final_file, 'rb') as f:
            bot.send_video(MY_ID, f, supports_streaming=True)
            
        if os.path.exists(raw_file): os.remove(raw_file)
        if os.path.exists(final_file): os.remove(final_file)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
                              
