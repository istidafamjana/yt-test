from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import random
import string
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)

# إعداد مجلد التحميلات
DOWNLOAD_FOLDER = tempfile.gettempdir()
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

def generate_random_name(extension='mp4'):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + f'.{extension}'

def clean_filename(filename):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

@app.route('/download', methods=['GET'])
def download_media():
    url = request.args.get('url')
    platform = request.args.get('platform', 'youtube')
    
    if not url:
        return jsonify({'error': 'يجب تقديم رابط URL'}), 400
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': False,
            'noplaylist': True,
            'socket_timeout': 30,
            'retries': 3,
            'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], generate_random_name('%(ext)s')),
            'cookiefile': 'cookies.txt',  # إضافة ملف الكوكيز
            'extractor_args': {
                'youtube': {
                    'skip': ['authcheck']  # تخطي التحقق من الصحة
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        }

        if platform == 'youtube':
            ydl_opts['format'] = 'best[height<=1080][ext=mp4]'
        elif platform == 'instagram':
            ydl_opts['format'] = 'best[ext=mp4][protocol=https]/best'
        elif platform == 'tiktok':
            ydl_opts['format'] = 'best[ext=mp4][protocol=https]'
        else:
            return jsonify({'error': 'نظام التشغيل غير معروف'}), 400

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if not info:
                return jsonify({'error': 'تعذر استخراج معلومات الفيديو'}), 500
                
            downloaded_file = ydl.prepare_filename(info)
            final_filename = clean_filename(os.path.basename(downloaded_file))
            final_path = os.path.join(app.config['DOWNLOAD_FOLDER'], final_filename)
            
            if os.path.exists(downloaded_file):
                os.rename(downloaded_file, final_path)
                return send_file(
                    final_path,
                    as_attachment=True,
                    download_name=final_filename,
                    mimetype='video/mp4' if final_filename.endswith('.mp4') else 'image/jpeg'
                )
            else:
                return jsonify({'error': 'فشل في التحميل (لم يتم إنشاء الملف)'}), 500

    except yt_dlp.utils.DownloadError as e:
        if "سجل الدخول لتأكيد أنك لست روبوتيًا" in str(e):
            return jsonify({
                'error': 'يوتيوب يطلب التحقق من أنك لست روبوتًا',
                'solution': 'جرب استخدام ملف كوكيز صالح أو انتظر بعض الوقت قبل المحاولة مرة أخرى'
            }), 403
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'message': 'API تحميل الفيديوهات',
        'usage': '/download?url=<رابط الفيديو>&platform=<youtube|instagram|tiktok>'
    })

if __name__ == '__main__':
    app.run(debug=True)
