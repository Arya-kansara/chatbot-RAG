from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename

from vector_search import store_document_chunks
from extract_pdf import extract_text_from_pdf
from explain_text import explain_text
from answer_question import answer_question
from text_to_speech import text_to_speech_bytes
from db import upload_audio

app = Flask(__name__)
app.secret_key = 'dev-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def home():
    session.pop('pdf_path', None)
    session.pop('pdf_name', None)
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('pdf_file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(pdf_path)
    session['pdf_path'] = pdf_path
    session['pdf_name'] = filename

    raw_text = extract_text_from_pdf(pdf_path)
    store_document_chunks(document_name=filename, full_text=raw_text)

    return jsonify({'filename': filename})


@app.route('/clear_file', methods=['POST'])
def clear_file():
    session.pop('pdf_path', None)
    session.pop('pdf_name', None)
    return jsonify({'message': 'PDF file cleared.'})


@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        lang_voice = data.get('voice', 'English-Male')
        language, gender = lang_voice.split('-')
        explain_full = data.get('explain_full', False)

        # Chat memory: the page sends the last messages of the open chat
        raw_history = data.get('history') or []
        history = [
            {"role": m["role"], "content": str(m["content"])[:1200]}
            for m in raw_history[-8:]
            if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")
        ]
        print("HISTORY ITEMS:", len(history), "| keys:", list(data.keys()))

        pdf_path = session.get('pdf_path')

        if explain_full:
            if not pdf_path:
                return jsonify({'error': 'No document attached.'}), 400
            raw_text = extract_text_from_pdf(pdf_path)
            result_text = explain_text(raw_text, language=language)

        elif pdf_path:
            if not user_question:
                return jsonify({'error': 'Please type your question.'}), 400
            raw_text = extract_text_from_pdf(pdf_path)
            pdf_name = session.get('pdf_name')
            result_text = answer_question(
                user_question,
                context_text=raw_text,
                document_name=pdf_name,
                language=language,
                history=history
            )

        else:
            if not user_question:
                return jsonify({'error': 'Please type your question.'}), 400
            result_text = answer_question(
                user_question,
                language=language,
                history=history
            )

        # Audio: a voice failure must not lose the text answer
        audio_url = None
        audio_error = None
        try:
            audio_filename = f"{uuid.uuid4().hex}.mp3"
            audio_bytes = asyncio.run(
                text_to_speech_bytes(result_text, language=language, gender=gender)
            )
            audio_url = upload_audio(audio_bytes, audio_filename)
        except Exception as e:
            audio_error = str(e)
            print("Audio failed:", e)

        return jsonify({
            'text': result_text,
            'audio_url': audio_url,
            'audio_error': audio_error
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)