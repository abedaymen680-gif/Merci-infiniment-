import os, subprocess, telebot, time, re

# التوكن الخاص بك
TOKEN = "8589322439:AAE7PESv8wSmSp5sOsVIfo60Uzs8KhrKkXw"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 بوت القناص جاهز!\n✅ تم اعتماد BashUpload كأسرع موقع رفع.\nأرسل الرابط الآن.")

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
        final_file = "video_output.mp4"
        
        status_msg = bot.send_message(MY_ID, "📥 **جاري سحب البث...**")

        # 1. سحب البث
        cmd_pull = ['ffmpeg', '-y', '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_at_eof', '1', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        subprocess.run(cmd_pull)

        # 2. الضغط (الحجم المثالي)
        bot.edit_message_text("⚙️ **جاري الضغط (CRF 33)...**", MY_ID, status_msg.message_id)
        cmd_comp = ['ffmpeg', '-y', '-i', raw_file, '-c:v', 'libx264', '-crf', '33', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', '-movflags', 'faststart', final_file]
        subprocess.run(cmd_comp)

        # 3. الرفع (باستخدام المواقع الفائزة في اختبارك)
        size = os.path.getsize(final_file) / (1024*1024)
        bot.edit_message_text(f"🚀 اكتمل الضغط ({size:.2f} MB). جاري استخراج الرابط...", MY_ID, status_msg.message_id)
        
        link = ""
        # المحاولة الأولى: BashUpload (الفائز بـ 0.77 ثانية)
        try:
            upload_cmd = f"curl -T {final_file} https://bashupload.com/{final_file}"
            output = subprocess.check_output(upload_cmd, shell=True).decode('utf-8')
            found_links = re.findall(r'https://bashupload.com/[^\s<"\' ]+', output)
            if found_links: link = found_links[0]
        except: pass

        # المحاولة الثانية: Literal (الفائز بـ 1.7 ثانية)
        if not link:
            try:
                upload_cmd = f"curl -F 'file=@{final_file}' https://literal.club/upload"
                output = subprocess.check_output(upload_cmd, shell=True).decode('utf-8')
                found_links = re.findall(r'https://literal.club/[^\s<"\' ]+', output)
                if found_links: link = found_links[0]
            except: pass

        if link:
            bot.send_message(MY_ID, f"✅ تم التسجيل بنجاح!\n📦 الحجم: {size:.2f} MB\n🔗 رابط التحميل:\n{link}")
        else:
            bot.send_message(MY_ID, "⚠️ فشل الرفع الخارجي، جاري الإرسال المباشر...")
            with open(final_file, 'rb') as f:
                bot.send_video(MY_ID, f)
            
        # تنظيف الملفات
        if os.path.exists(raw_file): os.remove(raw_file)
        if os.path.exists(final_file): os.remove(final_file)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
