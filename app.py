import os
import asyncio
from flask import Flask, render_template, request, jsonify , session
from werkzeug.utils import secure_filename
import uuid
from vector_search import store_document_chunks
from extract_pdf import extract_text_from_pdf
from explain_text import explain_text
from answer_question import answer_question
from text_to_speech import text_to_speech

app = Flask(__name__)
app.secret_key = 'dev-secret-key' # Needed for session management
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AUDIO_FOLDER'] = 'static/audio'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)


@app.route('/')
def home():
    session.pop('pdf_path', None)  # Clear any previous PDF path from session
    session.pop('pdf_name', None)  # Clear any previous PDF name from session
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
            result_text = answer_question(user_question, context_text=raw_text, document_name=pdf_name, language=language)

        else:
            if not user_question:
                return jsonify({'error': 'Please type your question.'}), 400
            result_text = answer_question(user_question, language=language)

        audio_filename = f"{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
        asyncio.run(text_to_speech(result_text, output_file=audio_path, language=language, gender=gender))

        return jsonify({
            'text': result_text,
            'audio_url': f'/static/audio/{audio_filename}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)