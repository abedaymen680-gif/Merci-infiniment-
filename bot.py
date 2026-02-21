import os, subprocess, telebot, time, re

TOKEN = "8589322439:AAE7PESv8wSmSp5sOsVIfo60Uzs8KhrKkXw"
MY_ID = 6849625315
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(MY_ID, "🚀 نظام القناص المطور (HEVC):\n✅ تم إصلاح خطأ الملف المفقود\n✅ ضغط H.265 مفعل")

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

        # 1. سحب البث
        cmd_pull = ['ffmpeg', '-y', '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_at_eof', '1', '-i', url, '-t', str(total_seconds), '-c', 'copy', raw_file]
        subprocess.run(cmd_pull)

        # 2. الضغط الحقيقي (HEVC) - تم تعديل الخيارات لضمان الاستقرار
        bot.edit_message_text("⚙️ **المرحلة 2: جاري الضغط بنظام HEVC...**", MY_ID, status_msg.message_id)
        
        # استخدمنا libx265 مع خيارات تضمن إنتاج الملف بدون أخطاء
        cmd_comp = [
            'ffmpeg', '-y', '-i', raw_file,
            '-c:v', 'libx265',
            '-crf', '28',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p', # مهم جداً للتوافق ومنع الأخطاء
            '-c:a', 'aac',
            '-tag:v', 'hvc1',
            final_file
        ]
        
        # تشغيل الضغط ومراقبة التقدم
        proc_comp = subprocess.Popen(cmd_comp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        last_update = 0
        for line in proc_comp.stdout:
            match = re.search(r"time=(\d+):(\d+):(\d+)", line)
            if match and (time.time() - last_update >= 10):
                h, m, s = map(int, match.groups())
                curr = h*3600 + m*60 + s
                p = min(int((curr/total_seconds)*100), 100)
                try: bot.edit_message_text(f"⚙️ **جاري الضغط (HEVC):**\n✅ المنجز: {p}%", MY_ID, status_msg.message_id)
                except: pass
                last_update = time.time()
        proc_comp.wait()

        # التأكد من وجود الملف قبل الرفع
        if not os.path.exists(final_file):
            raise Exception("فشل إنتاج ملف HEVC. قد لا يدعم السيرفر هذا النوع.")

        # 3. الرفع
        size = os.path.getsize(final_file) / (1024*1024)
        bot.edit_message_text(f"🚀 اكتمل الضغط ({size:.2f} MB). جاري الرفع...", MY_ID, status_msg.message_id)
        
        upload_cmd = f"curl -F 'file=@{final_file}' https://temp.sh/upload"
        link = subprocess.check_output(upload_cmd, shell=True).decode('utf-8').strip()

        if link and "http" in link:
            bot.send_message(MY_ID, f"✅ تم بنجاح!\n🎞️ الترميز: HEVC (H.265)\n📦 الحجم: {size:.2f} MB\n🔗 الرابط:\n{link}")
        else:
            bot.send_message(MY_ID, "⚠️ فشل الرفع، جاري المحاولة عبر تلجرام...")
            with open(final_file, 'rb') as f:
                bot.send_video(MY_ID, f)
            
        # تنظيف
        for f in [raw_file, final_file]:
            if os.path.exists(f): os.remove(f)
            
    except Exception as e:
        bot.send_message(MY_ID, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
