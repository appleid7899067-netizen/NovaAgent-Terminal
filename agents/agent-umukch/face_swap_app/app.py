from flask import Flask, request, render_template, send_from_directory
import os
from swap_faces import real_face_swap
from werkzeug.utils import secure_filename

app = Flask(__name__)
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Testing mode controls
TEST_MODE = os.environ.get('TEST_MODE', '1') == '1'
TEST_TOKEN = os.environ.get('TEST_TOKEN', 'TEST_TOKEN_ABC')  # replace with real token in your env

@app.route('/', methods=['GET','POST'])
def index():
    error = None
    swapped_url = None
    image1_url = None
    image2_url = None

    if TEST_MODE:
        token = request.headers.get('X-TEST-TOKEN') or request.args.get('token')
        if token != TEST_TOKEN:
            error = 'Testing mode: invalid or missing token. Use the correct X-TEST-TOKEN header or ?token=...'
            return render_template('index.html', error=error, swapped_url=None, image1_url=None, image2_url=None, test_banner=TEST_MODE)

    if request.method == 'POST':
        img1 = request.files.get('image1')
        img2 = request.files.get('image2')
        if not img1 or not img2:
            error = 'กรุณาอัปโหลดรูปภาพสองภาพ'
        else:
            path1 = os.path.join(UPLOAD_FOLDER, secure_filename(img1.filename))
            path2 = os.path.join(UPLOAD_FOLDER, secure_filename(img2.filename))
            img1.save(path1)
            img2.save(path2)
            out_filename = f"swapped_{secure_filename(img1.filename)}_{secure_filename(img2.filename)}.png"
            out_path = os.path.join(OUTPUT_FOLDER, out_filename)
            try:
                real_face_swap(path1, path2, out_path)
                swapped_url = f"outputs/{out_filename}"
            except Exception as e:
                error = str(e)
            image1_url = f"uploads/{os.path.basename(path1)}"
            image2_url = f"uploads/{os.path.basename(path2)}"
    return render_template('index.html', error=error, swapped_url=swapped_url, image1_url=image1_url, image2_url=image2_url, test_banner=TEST_MODE)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/outputs/<path:filename>')
def output_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
