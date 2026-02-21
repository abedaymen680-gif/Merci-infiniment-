import os, subprocess, telebot, time, re

# التوكن الخاص بك
TOKEN = "8589322439:AAE7PESv8wSmSp5sOsVIfo60Uzs8KhrKkXw"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "✅ تم التحديث! البوت يستخدم الآن Temp.sh للرفع المباشر.\nأرسل رابط الفيديو الآن.")

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
        final_file = "final_output.mp4"
        
        status_msg = bot.send_message(MY_ID, "📥 **المرحلة 1: جاري سحب البث...**")

        # 1. سحب البث
        cmd_pull = ['ffmpeg', '-y', '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_at_eof', '1', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        subprocess.run(cmd_pull)

        # 2. الضغط (الحجم الصغير)
        bot.edit_message_text("⚙️ **المرحلة 2: جاري الضغط (CRF 33)...**", MY_ID, status_msg.message_id)
        cmd_comp = ['ffmpeg', '-y', '-i', raw_file, '-c:v', 'libx264', '-crf', '33', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', '-movflags', 'faststart', final_file]
        subprocess.run(cmd_comp)

        # 3. الرفع على المواقع الناجحة في اختبارك
        size = os.path.getsize(final_file) / (1024*1024)
        bot.edit_message_text(f"🚀 اكتمل الضغط ({size:.2f} MB). جاري الرفع على Temp.sh...", MY_ID, status_msg.message_id)
        
        link = ""
        # المحاولة الأولى: Temp.sh (الذي نجح في الرفع بترمكس)
        try:
            upload_cmd = f"curl -F 'file=@{final_file}' https://temp.sh/upload"
            link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()
        except: pass

        # المحاولة الثانية: Transfer.sh (احتياطي)
        if not link or "http" not in link:
            try:
                upload_cmd = f"curl --upload-file {final_file} https://transfer.sh/{final_file}"
                link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()
            except: pass

        if link and "http" in link:
            bot.send_message(MY_ID, f"✅ تم بنجاح!\n📦 الحجم: {size:.2f} MB\n🔗 رابط التحميل المباشر:\n{link}")
        else:
            bot.send_message(MY_ID, "⚠️ فشل الرفع الخارجي، جاري الإرسال عبر تلجرام...")
            with open(final_file, 'rb') as f:
                bot.send_video(MY_ID, f)
            
        # تنظيف
        if os.path.exists(raw_file): os.remove(raw_file)
        if os.path.exists(final_file): os.remove(final_file)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
