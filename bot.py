import os, subprocess, telebot, time, re

# إعدادات البوت
TOKEN = "8589322439:AAE7PESv8wSmSp5sOsVIfo60Uzs8KhrKkXw"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🛡️ تم تشغيل نظام القناص الاحترافي\n━━━━━━━━━━━━━\n✅ ترميز HEVC (H.265) نشط\n✅ عداد السحب والضغط مفعل\n✅ الرفع المباشر: Temp.sh\n━━━━━━━━━━━━━\nأرسل رابط البث الآن.")

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
        final_file = "video_hevc.mp4"
        
        status_msg = bot.send_message(MY_ID, "📥 **المرحلة 1: جاري سحب البث...**")

        # 1. سحب البث مع عداد التقدم
        cmd_pull = [
            'ffmpeg', '-y', '-reconnect', '1', 
            '-reconnect_streamed', '1', '-reconnect_at_eof', '1', 
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
                try:
                    bot.edit_message_text(f"📥 **جاري السحب:**\n✅ المنجز: {p}% ({curr}/{total_seconds} ثانية)", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_pull.wait()

        # 2. الضغط بنظام HEVC (مثل كولاب) مع عداد التقدم
        bot.edit_message_text("⚙️ **المرحلة 2: جاري الضغط بنظام HEVC (H.265)...**", MY_ID, status_msg.message_id)
        
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265',
            '-crf', '28',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-tag:v', 'hvc1',
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
                try:
                    bot.edit_message_text(f"⚙️ **جاري الضغط (HEVC):**\n✅ المنجز: {p}%", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_comp.wait()

        # التأكد من نجاح إنتاج الملف
        if not os.path.exists(final_file):
            raise Exception("تعذر العثور على ملف الفيديو بعد الضغط!")

        # 3. الرفع والحصول على الرابط
        size = os.path.getsize(final_file) / (1024*1024)
        bot.edit_message_text(f"🚀 اكتمل الضغط بنجاح ({size:.2f} MB).\nجاري استخراج رابط التحميل المباشر...", MY_ID, status_msg.message_id)
        
        try:
            upload_cmd = f"curl -F 'file=@{final_file}' https://temp.sh/upload"
            link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()
        except:
            link = ""

        if link and "http" in link:
            bot.send_message(MY_ID, f"✅ **تمت المهمة بنجاح!**\n\n🎞️ الترميز: HEVC (H.265)\n📦 الحجم النهائي: {size:.2f} MB\n🔗 رابط التحميل المباشر:\n{link}")
        else:
            bot.send_message(MY_ID, "⚠️ فشل الرفع الخارجي، جاري الإرسال المباشر عبر تلجرام...")
            with open(final_file, 'rb') as f:
                bot.send_video(MY_ID, f, caption=f"🎞️ HEVC | 📦 {size:.2f} MB")
            
        # تنظيف الملفات المؤقتة
        if os.path.exists(raw_file): os.remove(raw_file)
        if os.path.exists(final_file): os.remove(final_file)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ في النظام: {e}")

bot.polling(none_stop=True)
