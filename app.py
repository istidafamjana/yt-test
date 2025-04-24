from flask import Flask, request, send_file
import yt_dlp
import os
import random
import string
import tempfile

app = Flask(__name__)

# إعدادات أساسية
DOWNLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_PLATFORMS = ['youtube', 'instagram', 'tiktok']

def generate_random_name(extension='mp4'):
    """إنشاء اسم ملف عشوائي"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + f'.{extension}'

@app.route('/download', methods=['GET'])
def download():
    # الحصول على المعلمات
    url = request.args.get('url')
    platform = request.args.get('platform', 'youtube').lower()
    
    # التحقق من المدخلات
    if not url:
        return {'error': 'يجب تقديم رابط URL'}, 400
    
    if platform not in ALLOWED_PLATFORMS:
        return {'error': f'نظام غير مدعوم. الاختيارات المتاحة: {", ".join(ALLOWED_PLATFORMS)}'}, 400

    # إعدادات yt-dlp حسب المنصة
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, generate_random_name('%(ext)s')),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    if platform == 'youtube':
        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]'
    elif platform == 'instagram':
        ydl_opts['format'] = 'best[ext=mp4]'
    elif platform == 'tiktok':
        ydl_opts['format'] = 'best[ext=mp4]'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # التنزيل الفعلي
            ydl.download([url])
            
            # العثور على الملف المحمل
            for file in os.listdir(DOWNLOAD_FOLDER):
                if file.startswith('tmp'):
                    file_path = os.path.join(DOWNLOAD_FOLDER, file)
                    return send_file(file_path, as_attachment=True)
            
            return {'error': 'لم يتم العثور على الملف المحمل'}, 500

    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
