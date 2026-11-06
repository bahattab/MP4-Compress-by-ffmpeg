# ضغط ملفات MP4 باستخدام FFmpeg

أداة بسيطة لضغط الفيديو من سطر الأوامر باستخدام FFmpeg. توفر خيارات H.264 وH.265، وتغيير الدقة أو معدل الإطارات، وحذف الصوت، واستهداف حجم تقريبي عبر ترميز H.264 على مرحلتين.

**الإصدار الحالي: 1.0.0**

## المتطلبات والإعداد

- Python 3.10 أو أحدث.
- FFmpeg و`ffprobe` في `PATH`.
- يدعم خيار H.265 وجود مشفر `libx265` في نسخة FFmpeg المثبتة.

Linux وmacOS:

```bash
chmod +x setup.sh
./setup.sh
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

تقوم ملفات الإعداد بتثبيت الأدوات الناقصة عبر مدير الحزم المتاح. أعد فتح الطرفية بعد تثبيت الأدوات إن لم يتعرف النظام عليها مباشرة.

## الاستخدام

```bash
python3 mp4_compress.py input.mp4 output.mp4
```

في Windows:

```powershell
python .\mp4_compress.py input.mp4 output.mp4
```

### أمثلة

ضغط متوازن باستخدام H.264، بقيمة CRF افتراضية 24 وصوت AAC بمعدل 128 kbps:

```bash
python3 mp4_compress.py input.mp4 output.mp4
```

H.265/HEVC لتقليل الحجم مع دعم أجهزة حديثة:

```bash
python3 mp4_compress.py input.mp4 output.mp4 --codec h265 --crf 28 --preset fast
```

تصغير الفيديو إلى 1080p أو 720p:

```bash
python3 mp4_compress.py input.mp4 output.mp4 --height 1080 --crf 23
python3 mp4_compress.py input.mp4 output.mp4 --height 720 --crf 24 --audio-bitrate 96k
```

استهداف حجم تقريبي 50 MB بترميز H.264 على مرحلتين:

```bash
python3 mp4_compress.py input.mp4 output.mp4 --target-size-mb 50
```

إزالة الصوت أو تقليل معدل الإطارات:

```bash
python3 mp4_compress.py input.mp4 output.mp4 --crf 26 --no-audio
python3 mp4_compress.py input.mp4 output.mp4 --crf 26 --fps 24 --audio-bitrate 96k
```

عرض جميع الخيارات:

```bash
python3 mp4_compress.py --help
```

## أفضل أوامر FFmpeg لتقليل حجم الفيديو

تعتمد أفضل طريقة على التوازن بين الجودة وسرعة المعالجة والحجم المستهدف. تتحكم قيمة **CRF** بالجودة والحجم: القيمة الأعلى تنتج ملفاً أصغر وجودة أقل. المجال الشائع لـH.264 هو 23 إلى 28، و23 يعطي جودة عالية عادةً.

### 1. ضغط متوازن باستخدام H.264

```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 24 -preset medium -c:a aac -b:a 128k output.mp4
```

- `-c:v libx264`: ترميز الفيديو بـH.264 واسع التوافق.
- `-crf 24`: يحدد مستوى الضغط البصري.
- `-preset medium`: يوازن سرعة الترميز وكفاءته. استخدم `slow` لضغط أفضل أو `fast` لسرعة أكبر.
- `-c:a aac -b:a 128k`: ترميز الصوت AAC بمعدل 128 kbps.

### 2. ضغط أعلى كفاءة باستخدام H.265 / HEVC

```bash
ffmpeg -i input.mp4 -c:v libx265 -crf 28 -preset fast -c:a aac -b:a 128k output.mp4
```

يستخدم `libx265` ترميز HEVC. قد يحقق توفيراً كبيراً بالحجم مقارنة بـH.264 عند جودة مقاربة، لكن النتيجة تعتمد على محتوى الفيديو، وإعدادات الترميز، ودعم الجهاز. القيمة `-crf 28` نقطة بداية مناسبة وليست معادلة ثابتة لـH.264 CRF 23.

### 3. تقليل الدقة مع الضغط

```bash
ffmpeg -i input.mp4 -vf "scale=-2:1080" -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4
ffmpeg -i input.mp4 -vf "scale=-2:720" -c:v libx264 -crf 24 -c:a aac -b:a 96k output.mp4
```

القيمة `-2` تحافظ على نسبة الأبعاد وتجعل العرض قابلاً للقسمة على 2، وهو مناسب لمشفّرات H.264/H.265.

### 4. استهداف حجم باستخدام ترميز Two-Pass

احسب معدل البت الإجمالي التقريبي هكذا:

```text
معدل البت الإجمالي (kbps) = (الحجم المستهدف بالبايت × 8) ÷ (المدة بالثواني × 1000)
```

للحصول على معدل الفيديو، اطرح معدل الصوت واحتياطياً بسيطاً لحاوية MP4 من الناتج. مثال توضيحي بمعدل فيديو مستهدف 1000 kbps:

```bash
# المرحلة الأولى: تحليل الفيديو
ffmpeg -y -i input.mp4 -c:v libx264 -b:v 1000k -pass 1 -an -f null /dev/null

# المرحلة الثانية: إنشاء الملف
ffmpeg -i input.mp4 -c:v libx264 -b:v 1000k -pass 2 -c:a aac -b:a 128k output.mp4
```

في Windows استبدل `/dev/null` بـ`NUL`. قد يختلف الحجم النهائي قليلاً بسبب الصوت وبيانات الحاوية.

### 5. خيارات إضافية

حذف الصوت:

```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 26 -an output.mp4
```

تقليل معدل الإطارات إلى 24 إطاراً بالثانية:

```bash
ffmpeg -i input.mp4 -r 24 -c:v libx264 -crf 26 -c:a aac -b:a 96k output.mp4
```

## ملفات المشروع

- `mp4_compress.py`: أداة الضغط.
- `setup.sh`: إعداد FFmpeg وPython على Linux وmacOS.
- `setup.ps1`: إعداد FFmpeg وPython على Windows.
- `README.md`: هذا الدليل وأوامر FFmpeg المرجعية.

## مصادر FFmpeg

- [دليل ترميز H.264](https://trac.ffmpeg.org/wiki/Encode/H.264)
- [دليل ترميز H.265](https://trac.ffmpeg.org/wiki/Encode/H.265)
- [وثائق FFmpeg الرسمية](https://ffmpeg.org/ffmpeg.html)

## الترخيص

المشروع مرخص وفق MIT؛ راجع ملف `LICENSE`.
