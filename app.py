from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import random
import string
import time
import tempfile

app = Flask(__name__)

# إعدادات متقدمة لتجنب الحظر
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def generate_random_name(extension='mp4'):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + f'.{extension}'

@app.route('/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'يجب تقديم رابط URL'}), 400

    try:
        # إعدادات yt-dlp المتقدمة
        ydl_opts = {
            'format': 'best[height<=1080][ext=mp4]',
            'outtmpl': os.path.join(tempfile.gettempdir(), generate_random_name('%(ext)s')),
            'quiet': True,
            'no_warnings': False,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_args': {
                'youtube': {
                    'skip': ['authcheck', 'agegate', 'password']
                }
            },
            'http_headers': {
                'User-Agent': get_random_user_agent(),
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com'
            },
            'sleep_interval': random.randint(2, 5),
            'force_ipv4': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'ignoreerrors': True
        }

        # إضافة تأخير عشوائي
        time.sleep(random.uniform(1.0, 3.0))

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if not info:
                return jsonify({'error': 'تعذر استخراج معلومات الفيديو'}), 500

            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=os.path.basename(filename),
                    mimetype='video/mp4'
                )
            else:
                return jsonify({'error': 'فشل في تحميل الملف'}), 500

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "سجّل الدخول لتأكيد أنك لست روبوتًا" in error_msg:
            return jsonify({
                'error': 'يوتيوب يطلب التحقق من الهوية',
                'solution': [
                    '1. جرب تغيير عنوان IP الخاص بك',
                    '2. انتظر 1-2 ساعة قبل المحاولة مرة أخرى',
                    '3. جرب استخدام VPN من موقع جغرافي مختلف'
                ]
            }), 403
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'usage': '/download?url=YOUTUBE_URL',
        'note': 'قد يحتاج بعض الفيديوهات إلى تحقق يدوي من يوتيوب'
    })

if __name__ == '__main__':
    app.run(debug=True)
