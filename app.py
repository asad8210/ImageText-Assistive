import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from gtts import gTTS
from langdetect import detect
import threading
from functools import lru_cache
import time

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

def save_tts_audio(text, lang, path):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(path)
    except Exception as e:
        print(f"[TTS ERROR] {e}")

def delete_files_later(image_path, audio_path, delay=600):
    def delete():
        time.sleep(delay)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            print(f"Deleted files: {image_path}, {audio_path}")
        except Exception as e:
            print(f"File delete error: {e}")
    threading.Thread(target=delete).start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files or request.files['image'].filename == '':
            return redirect(url_for('index'))

        file = request.files['image']
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        # OCR
        img = Image.open(image_path).convert("RGB")
        extracted_text = pytesseract.image_to_string(img, lang='hin+eng')

        # Language detection
        try:
            detected_lang = detect(extracted_text)
        except:
            detected_lang = 'en'
        gtts_lang = 'hi' if detected_lang == 'hi' else 'en'

        # Braille translation
        braille_body = text_to_braille(extracted_text)
        braille_prefix = '⠰⠓ ' if gtts_lang == 'hi' else '⠰⠑ '
        braille_text = braille_prefix + braille_body

        # TTS save
        audio_filename = filename.rsplit('.', 1)[0] + '.mp3'
        audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
        save_tts_audio(extracted_text, gtts_lang, audio_path)

        # Clean up later
        delete_files_later(image_path, audio_path)

        return render_template('index.html',
                               original_image=f'uploads/{filename}',
                               extracted_text=extracted_text,
                               braille_text=braille_text,
                               audio_file=f'audio/{audio_filename}')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
