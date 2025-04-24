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
    """إنشاء اسم عشوائي للملف مع الاحتفاظ بالامتداد"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + f'.{extension}'

def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المسموحة"""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

@app.route('/download', methods=['GET'])
def download_media():
    url = request.args.get('url')
    platform = request.args.get('platform', 'youtube')  # youtube, instagram, tiktok
    
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
            
            downloaded_file = ydl.prepare_filename(info)
            final_filename = clean_filename(os.path.basename(downloaded_file))
            final_path = os.path.join(app.config['DOWNLOAD_FOLDER'], final_filename)
            
            if os.path.exists(downloaded_file):
                os.rename(downloaded_file, final_path)
                
                # إرجاع الملف المحمل
                return send_file(
                    final_path,
                    as_attachment=True,
                    download_name=final_filename,
                    mimetype='video/mp4' if final_filename.endswith('.mp4') else 'image/jpeg'
                )
            else:
                return jsonify({'error': 'فشل في التحميل (لم يتم إنشاء الملف)'}), 500

    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500

@app.route('/')
def home():
    return """
    <h1>API تحميل الفيديوهات</h1>
    <p>استخدم /download مع المعلمات:</p>
    <ul>
        <li>url: رابط الفيديو</li>
        <li>platform: youtube أو instagram أو tiktok</li>
    </ul>
    <p>مثال: /download?url=رابط_الفيديو&platform=youtube</p>
    """

if __name__ == '__main__':
    app.run(debug=True)
