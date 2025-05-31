import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from gtts import gTTS
from langdetect import detect
import threading
from functools import lru_cache

app = Flask(__name__)

# Configure upload and audio folders
UPLOAD_FOLDER = 'static/uploads'
AUDIO_FOLDER = 'static/audio'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

# Braille character map for English and Hindi
braille_map = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽',
    'z': '⠵',
    ' ': ' ', '\n': '\n', ',': '⠂', '.': '⠲', '?': '⠦', '!': '⠖',

    # Hindi vowels, consonants, and other signs
    "अ": "⠁", "आ": "⠡", "इ": "⠊", "ई": "⠒", "उ": "⠥",
    "ऊ": "⠳", "ए": "⠑", "ऐ": "⠣", "ओ": "⠕", "औ": "⠷",
    "ऋ": "⠗", "क": "⠅", "ख": "⠩", "ग": "⠛", "घ": "⠣",
    "ङ": "⠻", "च": "⠉", "छ": "⠡", "ज": "⠚", "झ": "⠒",
    "ञ": "⠱", "ट": "⠞", "ठ": "⠾", "ड": "⠙", "ढ": "⠹",
    "ण": "⠻", "त": "⠞", "थ": "⠮", "द": "⠙", "ध": "⠹",
    "न": "⠝", "प": "⠏", "फ": "⠟", "ब": "⠃", "भ": "⠫",
    "म": "⠍", "य": "⠽", "र": "⠗", "ल": "⠇", "व": "⠧",
    "श": "⠱", "ष": "⠳", "स": "⠎", "ह": "⠓", "क्ष": "⠟",
    "ज्ञ": "⠻", "ड़": "⠚", "ढ़": "⠚", "फ़": "⠋", "ज़": "⠵",
    "ग्य": "⠛⠽", "त्र": "⠞⠗", "श्र": "⠱⠗",

    "ा": "⠡", "ि": "⠊", "ी": "⠒", "ु": "⠥", "ू": "⠳",
    "े": "⠑", "ै": "⠣", "ो": "⠕", "ौ": "⠷", "ृ": "⠗",

    "्": "⠄", "ं": "⠈", "ः": "⠘", "ँ": "⠨",

    "०": "⠚", "१": "⠁", "२": "⠃", "३": "⠉", "४": "⠙",
    "५": "⠑", "६": "⠋", "७": "⠛", "८": "⠓", "९": "⠊",

    "।": "⠲", ",": "⠂", "?": "⠦", "!": "⠖", "\"": "⠶",
    "'": "⠄", ";": "⠆", ":": "⠒", ".": "⠲", "-": "⠤",
    "(": "⠶", ")": "⠶", "/": "⠌",

    "A": "⠁", "B": "⠃", "C": "⠉", "D": "⠙", "E": "⠑",
    "F": "⠋", "G": "⠛", "H": "⠓", "I": "⠊", "J": "⠚",
    "K": "⠅", "L": "⠇", "M": "⠍", "N": "⠝", "O": "⠕",
    "P": "⠏", "Q": "⠟", "R": "⠗", "S": "⠎", "T": "⠞",
    "U": "⠥", "V": "⠧", "W": "⠺", "X": "⠭", "Y": "⠽", "Z": "⠵",
}

@lru_cache(maxsize=128)
def text_to_braille(text):
    return ''.join(braille_map.get(ch, ' ') for ch in text)

@app.route('/')
def index():
    return render_template('index.html')

def save_tts_audio(text, lang, path):
    """Generate and save audio in a separate thread to avoid blocking."""
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(path)
    except Exception as e:
        print(f"[TTS ERROR] {e}")

@app.route('/process', methods=['POST'])
def process():
    if 'image' not in request.files or request.files['image'].filename == '':
        return redirect(url_for('index'))

    file = request.files['image']
    filename = secure_filename(file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(image_path)

    # ✅ Open image and extract text (fastest with RGB mode)
    img = Image.open(image_path).convert("RGB")
    extracted_text = pytesseract.image_to_string(img, lang='hin+eng')

    # ✅ Try to detect language
    try:
        detected_lang = detect(extracted_text)
    except:
        detected_lang = 'en'
    gtts_lang = 'hi' if detected_lang == 'hi' else 'en'

    # ✅ Braille translation
    braille_text_body = text_to_braille(extracted_text)
    braille_prefix = '⠰⠓ ' if detected_lang == 'hi' else '⠰⠑ '
    braille_text = braille_prefix + braille_text_body

    # ✅ Convert text to speech (async thread)
    audio_filename = filename.rsplit('.', 1)[0] + '.mp3'
    audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
    tts_thread = threading.Thread(target=save_tts_audio, args=(extracted_text, gtts_lang, audio_path))
    tts_thread.start()

    return render_template('result.html',
                           original_image=f'uploads/{filename}',
                           extracted_text=extracted_text,
                           braille_text=braille_text,
                           audio_file=f'audio/{audio_filename}')
                           
if __name__ == '__main__':
    # ✅ Enable threaded to allow async tasks to work faster
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)