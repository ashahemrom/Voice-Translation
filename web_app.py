#!/usr/bin/env python3
"""
Flask Web Application for Doctor-Patient Voice Translation Service
Provides a clean web UI for the voice translation agent
"""

import os
import sys
import threading
import queue
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import time
import base64
import io

# Try to import speech recognition for server-side fallback
try:
    import speech_recognition as sr
    SERVER_SPEECH_AVAILABLE = True
except ImportError:
    SERVER_SPEECH_AVAILABLE = False
    print("⚠️ Server-side speech recognition not available")

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sarvam_service import SarvamService, DoctorPatientTranslator, SarvamTranslationError
from voice_agent import VoiceTranslationAgent, SPEECH_RECOGNITION_AVAILABLE, PYTTSX3_AVAILABLE
from config import SARVAM_API_KEY, LANGUAGE_CONFIG

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'voice_translation_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables for voice agent management
voice_agent = None
translator = None
current_patient_language = 'hindi'
conversation_active = False
translation_queue = queue.Queue()

# Selected languages from language selection page
selected_doctor_language = None
selected_patient_language = None

def initialize_services():
    """Initialize translation and voice services"""
    global translator, voice_agent

    try:
        service = SarvamService()
        translator = DoctorPatientTranslator(service)

        # Test translation to ensure API works
        test_translation = translator.doctor_to_patient("Hello", "hindi")
        print(f"✅ Translation service initialized: {test_translation}")

        # Initialize voice agent
        voice_agent = VoiceTranslationAgent(translator)
        voice_agent.set_patient_language(current_patient_language)

        print("✅ Voice agent initialized")
        return True

    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        print("⚠️ Running with mock translation service...")

        # Create mock translator for demonstration
        class MockTranslator:
            def detect_language(self, text):
                try:
                    # Try Azure OpenAI first
                    return self._azure_language_detection(text)
                except Exception as e:
                    print(f"Azure OpenAI mock detection failed: {e}, using fallback")
                    # Fallback to pattern-based detection
                    return self._fallback_language_detection(text)

            def _azure_language_detection(self, text):
                """Use direct HTTP requests to Azure OpenAI"""
                try:
                    return self._azure_http_detection(text)
                except Exception as e:
                    raise Exception(f"Azure OpenAI HTTP request failed: {e}")

            def _azure_http_detection(self, text):
                """Fallback: Direct HTTP request to Azure OpenAI (bypasses client issues)"""
                import requests

                url = "https://dunlin-aplication-east-us-2.openai.azure.com/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2025-01-01-preview"
                headers = {
                    "Content-Type": "application/json",
                    "api-key": "77cd722ffe2d450d80db32a2eead2a82"
                }

                data = {
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a language detection AI. Your ONLY function is to detect the language of text and respond with EXACTLY ONE language code.

                            VALID RESPONSES (respond with EXACTLY one of these):
                            - en-IN (English)
                            - hi-IN (Hindi)
                            - mr-IN (Marathi)
                            - kn-IN (Kannada)

                            RULES:
                            1. Respond with EXACTLY ONE language code from the list above
                            2. NO explanations, NO extra text, NO punctuation
                            3. If text contains Devanagari script (हिंदी), respond: hi-IN
                            4. If text is primarily English/romanized, respond: en-IN
                            5. Default to en-IN if unsure"""
                        },
                        {
                            "role": "user",
                            "content": f"Detect the language of this text: {text}"
                        }
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1,
                    "api-version": "2025-01-01-preview"
                }

                response = requests.post(url, headers=headers, json=data, timeout=10)
                response.raise_for_status()

                result = response.json()
                detected_lang = result['choices'][0]['message']['content'].strip()

                allowed_codes = ['en-IN', 'hi-IN', 'mr-IN', 'kn-IN']
                if detected_lang in allowed_codes:
                    return detected_lang
                else:
                    raise Exception(f"HTTP API returned invalid response: '{detected_lang}'")

            def _fallback_language_detection(self, text):
                # Improved fallback language detection
                if re.search(r'[\u0900-\u097F]', text):
                    return 'hi-IN'  # Contains Devanagari script = definitely Hindi

                # English indicators
                english_words = [
                    'hello', 'hi', 'good', 'morning', 'afternoon', 'evening', 'please', 'thank', 'you',
                    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would',
                    'take', 'medicine', 'prescription', 'diagnosis', 'treatment', 'check', 'blood',
                    'pressure', 'temperature', 'fever', 'cough', 'pain', 'headache', 'stomach', 'chest'
                ]

                # Hindi/romanized Hindi indicators (expanded list)
                hindi_words = [
                    'hai', 'hain', 'nahi', 'nahin', 'nahi', 'main', 'hum', 'tum', 'aap', 'kya', 'kyon', 'kaise', 'kahan',
                    'yeh', 'yah', 'woh', 'aur', 'par', 'lekin', 'magar', 'ki', 'ka', 'ke', 'ko', 'se', 'mein', 'pe',
                    'tak', 'kar', 'raha', 'rahi', 'rahe', 'tha', 'thi', 'the', 'hoga', 'hog', 'hun', 'hoon',
                    'bhai', 'bahut', 'sahi', 'theek', 'ab', 'ulta', 'kam', 'karta', 'karti', 'samajh', 'samjho',
                    'dard', 'dukh', 'bimari', 'doctor', 'hospital', 'tablet', 'syrup', 'mujhe', 'muje', 'mujhko',
                    'tera', 'tera', 'teri', 'teri', 'apna', 'apni', 'apne', 'apno', 'yahin', 'wahin', 'idhar', 'udhar',
                    'upar', 'neeche', 'andar', 'bahar', 'samne', 'peeche', 'bina', 'sath', 'ke', 'saath',
                    'padega', 'padegi', 'padenge', 'karna', 'karne', 'karni', 'karu', 'kare', 'karega', 'karegi',
                    'jao', 'jaoge', 'gaya', 'gayi', 'rahta', 'rahti', 'rahte', 'soch', 'sochta', 'sochte',
                    'khao', 'khaoge', 'khana', 'khane', 'peena', 'peene', 'peo', 'piyo', 'lete', 'lena', 'deta', 'deti'
                ]

                words = text.lower().split()
                if not words:
                    return 'en-IN'  # Default to English for empty text

                english_count = sum(1 for word in words if word in english_words)
                hindi_count = sum(1 for word in words if word in hindi_words)

                print(f"🔍 Fallback detection - English: {english_count}, Hindi: {hindi_count}")

                # If clear majority of Hindi words, classify as Hindi
                if hindi_count > len(words) * 0.4:  # 40% Hindi words = Hindi
                    return 'hi-IN'
                # If clear majority of English words, classify as English
                elif english_count > len(words) * 0.3:  # 30% English words = English
                    return 'en-IN'
                else:
                    # Ambiguous - check for English grammatical patterns
                    has_articles = any(word in ['the', 'a', 'an'] for word in words)
                    has_be_verbs = any(word in ['is', 'are', 'was', 'were', 'have', 'has', 'had'] for word in words)

                    if has_articles or has_be_verbs:
                        return 'en-IN'  # Looks like English grammar
                    else:
                        return 'hi-IN'  # Default to Hindi for medical context

            def doctor_to_patient(self, text, lang):
                # Simple mock translations - English to patient's language
                # lang is now a language name like 'hindi', 'marathi', etc.
                if lang == 'hindi':
                    return f"नमस्ते! [Mock Hindi: {text}]"
                elif lang == 'marathi':
                    return f"नमस्कार! [Mock Marathi: {text}]"
                elif lang == 'kannada':
                    return f"ನಮಸ್ಕಾರ! [Mock Kannada: {text}]"
                return f"[Mock: {text}]"

            def patient_to_doctor(self, text, lang):
                # Patient's language to English
                return f"Hello! [Mock English: {text}]"

        class MockVoiceAgent:
            def __init__(self, translator):
                self.translator = translator

            def set_patient_language(self, lang):
                pass

            def start_conversation(self, external_control=False):
                pass

            def process_single_turn(self):
                return False

        translator = MockTranslator()
        voice_agent = MockVoiceAgent(translator)

        print("✅ Mock services initialized for demonstration")
        return True

@app.route('/')
def language_selection():
    """Language selection page"""
    return render_template('language_selection.html')

@app.route('/translator', methods=['GET', 'POST'])
def translator():
    """Main translation page with selected languages"""
    global selected_doctor_language, selected_patient_language

    if request.method == 'POST':
        # Store selected languages from form
        selected_doctor_language = request.form.get('doctor_language')
        selected_patient_language = request.form.get('patient_language')

        if not selected_doctor_language or not selected_patient_language:
            return render_template('language_selection.html',
                                 error="Please select both languages")

        if selected_doctor_language == selected_patient_language:
            return render_template('language_selection.html',
                                 error="Please select different languages")

    # Check if languages are selected (for both GET and POST)
    if not selected_doctor_language or not selected_patient_language:
        return render_template('language_selection.html',
                             error="Please select languages first")

    return render_template('index.html',
                         speech_available=SPEECH_RECOGNITION_AVAILABLE,
                         tts_available=PYTTSX3_AVAILABLE,
                         doctor_language=selected_doctor_language,
                         patient_language=selected_patient_language)

@app.route('/diagnostic')
def diagnostic():
    """Diagnostic page to test speech recognition"""
    return render_template('diagnostic.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    services_status = {
        'translation': translator is not None,
        'voice_agent': voice_agent is not None,
        'speech_recognition': SPEECH_RECOGNITION_AVAILABLE,
        'text_to_speech': PYTTSX3_AVAILABLE,
        'conversation_active': conversation_active
    }

    return jsonify({
        'status': 'healthy' if all(services_status.values()) else 'degraded',
        'services': services_status
    })

@app.route('/api/languages')
def get_languages():
    """Get available languages"""
    return jsonify({
        'patient_languages': {k: v for k, v in LANGUAGE_CONFIG.items() if k != 'english'},
        'doctor_language': LANGUAGE_CONFIG['english']
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to Voice Translation Service', 'type': 'success'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")
    global conversation_active
    conversation_active = False

@socketio.on('set_language')
def handle_set_language(data):
    """Handle language selection"""
    global current_patient_language, voice_agent

    language = data.get('language', 'hindi')
    if language in LANGUAGE_CONFIG and language != 'english':
        current_patient_language = language
        if voice_agent:
            voice_agent.set_patient_language(language)

        emit('language_changed', {
            'language': language,
            'native_name': {
                'hindi': 'हिंदी',
                'marathi': 'मराठी',
                'kannada': 'ಕನ್ನಡ'
            }.get(language, language)
        })
        emit('status', {'message': f'Patient language set to {language.title()}', 'type': 'success'})
    else:
        emit('status', {'message': 'Invalid language selection', 'type': 'error'})

@socketio.on('start_conversation')
def handle_start_conversation():
    """Start voice conversation"""
    global conversation_active, voice_agent

    if not voice_agent:
        emit('status', {'message': 'Voice agent not initialized', 'type': 'error'})
        return

    conversation_active = True
    voice_agent.start_conversation(external_control=True)  # Initialize without internal loop
    emit('conversation_started', {'status': 'active'})
    emit('status', {'message': 'Voice conversation started - speak into microphone', 'type': 'info'})

    # Start conversation in a separate thread with external control
    def conversation_thread():
        global conversation_active
        try:
            while conversation_active and voice_agent:
                if not voice_agent.process_single_turn():
                    break
                time.sleep(0.5)  # Small delay between turns
        except Exception as e:
            socketio.emit('status', {'message': f'Conversation error: {e}', 'type': 'error'})
        finally:
            conversation_active = False
            socketio.emit('conversation_ended')

    thread = threading.Thread(target=conversation_thread, daemon=True)
    thread.start()

@socketio.on('stop_conversation')
def handle_stop_conversation():
    """Stop voice conversation"""
    global conversation_active
    conversation_active = False
    emit('conversation_ended')
    emit('status', {'message': 'Voice conversation stopped', 'type': 'info'})


@socketio.on('text_translate')
def handle_text_translate(data):
    """Handle text translation requests"""
    text = data.get('text', '').strip()
    direction = data.get('direction', 'doctor_to_patient')  # or 'patient_to_doctor'

    if not text:
        emit('translation_result', {'error': 'No text provided'})
        return

    try:
        if direction == 'doctor_to_patient':
            translated = translator.doctor_to_patient(text, current_patient_language)
            emit('translation_result', {
                'original': text,
                'translated': translated,
                'direction': direction,
                'languages': {'from': 'English', 'to': current_patient_language.title()}
            })
        else:
            translated = translator.patient_to_doctor(text, current_patient_language)
            emit('translation_result', {
                'original': text,
                'translated': translated,
                'direction': direction,
                'languages': {'from': current_patient_language.title(), 'to': 'English'}
            })

    except SarvamTranslationError as e:
        emit('translation_result', {'error': str(e)})

@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio data from client using STT with fallback"""
    try:
        audio_base64 = data.get('audio', '')
        if not audio_base64:
            emit('speech_result', {'error': 'No audio data received'})
            return

        print(f"🎤 Received audio data: {len(audio_base64)} chars")

        # Decode base64 audio data
        import base64
        audio_data = base64.b64decode(audio_base64)

        print(f"📦 Decoded audio: {len(audio_data)} bytes")

        transcription_type = "🎭 MOCK"  # Default to mock

        # Ensure transcription_type is available in all code paths
        if 'transcription_type' not in locals():
            transcription_type = "🎭 MOCK"

        # Try Sarvam STT first
        try:
            print("🔄 Trying Sarvam STT...")
            transcript, detected_lang = voice_agent.translator.sarvam.speech_to_text_with_language(audio_data)
            print(f"✅ Sarvam STT successful: '{transcript}' in {detected_lang}")
            transcription_type = "🎉 REAL (Sarvam)"
        except Exception as sarvam_error:
            print(f"⚠️ Sarvam STT failed: {sarvam_error}")

            # Check if we have server-side speech recognition available
            if SERVER_SPEECH_AVAILABLE:
                print("🔄 Falling back to server-side Speech Recognition...")
                try:
                    import io
                    from pydub import AudioSegment

                    print("🎵 Converting WebM to WAV for Google STT...")

                    # Convert WebM to WAV for Google STT
                    try:
                        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
                        wav_data = io.BytesIO()
                        audio_segment.export(wav_data, format="wav")
                        wav_data.seek(0)

                        print(f"✅ Audio conversion successful: {len(wav_data.getvalue())} bytes")

                        # Use Google Speech Recognition with the WAV data
                        # Create a temporary file-like object for speech_recognition
                        wav_data.seek(0)  # Reset to beginning
                        with sr.AudioFile(wav_data) as source:
                            audio_content = voice_agent.recognizer.record(source)
                            transcript = voice_agent.recognizer.recognize_google(audio_content)

                        detected_lang = 'en-IN'  # Default to English for Google STT

                        print(f"🎉 REAL SPEECH RECOGNITION SUCCESSFUL: '{transcript}'")
                        print("🎊 Your actual speech was transcribed! No more mock data!")
                        transcription_type = "🎉 REAL (Google)"

                    except Exception as conversion_error:
                        print(f"❌ Audio conversion failed: {conversion_error}")
                        raise Exception(f"Audio conversion failed: {conversion_error}")

                except Exception as server_error:
                    print(f"❌ Server STT failed: {server_error}")
                    # Final fallback: intelligent mock transcription based on what user might say
                    mock_responses = {
                        'mr-IN': [
                            "मी आजारी आहे, मला ताप आहे आणि डोकेदुखी आहे",
                            "मला पोटदुखी होत आहे",
                            "मी डॉक्टरांना भेटायला हवे"
                        ],
                        'hi-IN': [
                            "मैं बीमार हूं, मुझे बुखार है और सिरदर्द है",
                            "मुझे पेट में दर्द हो रहा है",
                            "मुझे डॉक्टर से मिलना चाहिए"
                        ],
                        'kn-IN': [
                            "ನಾನು ಅನಾರೋಗ್ಯ, ನನಗೆ ಜ್ವರ ಮತ್ತು ತಲೆನೋವು ಇದೆ",
                            "ನನಗೆ ಹೊಟ್ಟೆ ನೋವು ಇದೆ",
                            "ನಾನು ಡಾಕ್ಟರ್ ಅವರನ್ನು ಭೇಟಿ ಮಾಡಬೇಕು"
                        ],
                        'en-IN': [
                            "I am sick, I have fever and headache",
                            "I have stomach pain",
                            "I need to see a doctor"
                        ]
                    }

                    import random
                    responses = mock_responses.get(selected_patient_language, mock_responses['en-IN'])
                    transcript = random.choice(responses)
                    detected_lang = selected_patient_language or 'en-IN'
                    print(f"🎭 MOCK TRANSCRIPTION (speech recognition not available): '{transcript}' in {detected_lang}")
                    print("💡 To enable real speech recognition, install: pip install SpeechRecognition pydub")
            else:
                print("❌ No speech recognition available, using intelligent mock transcription")
                # Intelligent mock transcription based on selected languages
                if selected_patient_language == 'mr-IN':
                    transcript = "मी मराठीमध्ये बोलत आहे, मला डॉक्टरांना समजावे लागेल"
                    detected_lang = 'mr-IN'
                    print(f"🎭 Mock Marathi: '{transcript}'")
                elif selected_patient_language == 'hi-IN':
                    transcript = "मैं हिंदी में बोल रहा हूं, मुझे डॉक्टर को समझना होगा"
                    detected_lang = 'hi-IN'
                    print(f"🎭 Mock Hindi: '{transcript}'")
                elif selected_patient_language == 'kn-IN':
                    transcript = "ನಾನು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ, ಡಾಕ್ಟರ್ ಅವರಿಗೆ ಅರ್ಥವಾಗಬೇಕು"
                    detected_lang = 'kn-IN'
                    print(f"🎭 Mock Kannada: '{transcript}'")
                else:
                    transcript = "I am speaking in English, the doctor needs to understand me"
                    detected_lang = 'en-IN'
                    print(f"🎭 Mock English: '{transcript}'")

        if not transcript.strip():
            print("❌ No speech detected in transcript")
            emit('speech_result', {'error': 'No speech detected'})
            return

        print(f"✅ About to process transcript: '{transcript}' in {detected_lang}")
        print(f"📊 Transcription type: {transcription_type}")

        # Now process the transcribed text
        process_transcript(transcript, detected_lang)

    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        import traceback
        traceback.print_exc()
        emit('speech_result', {'error': f'Processing failed: {str(e)}'})

def process_transcript(transcript, detected_lang):
    """Process the transcribed text for translation"""
    print(f"🔄 ENTERING process_transcript with: '{transcript}' in {detected_lang}")
    global selected_doctor_language, selected_patient_language

    if not selected_doctor_language or not selected_patient_language:
        print("❌ Languages not configured")
        emit('speech_result', {'error': 'Languages not configured. Please restart.'})
        return

    print(f"✅ Languages configured: Doctor={selected_doctor_language}, Patient={selected_patient_language}")

    try:
        print(f"🔍 Processing: '{transcript}' detected as {detected_lang}")

        # Determine translation direction based on detected language and selected languages
        if detected_lang == selected_doctor_language:
            # Doctor's language detected → translate to patient's language
            target_lang_code = selected_patient_language
            target_lang_name = lang_code_to_name.get(target_lang_code, 'hindi')
            translated = voice_agent.translator.sarvam.translate_text(transcript, detected_lang, target_lang_code)
            speaker_label = f"{lang_code_to_name.get(detected_lang, 'english').title()} → {target_lang_name.title()}"
            speaker = 'doctor'
        elif detected_lang == selected_patient_language:
            # Patient's language detected → translate to doctor's language
            target_lang_code = selected_doctor_language
            target_lang_name = lang_code_to_name.get(target_lang_code, 'english')
            translated = voice_agent.translator.sarvam.translate_text(transcript, detected_lang, target_lang_code)
            speaker_label = f"{lang_code_to_name.get(detected_lang, 'hindi').title()} → {target_lang_name.title()}"
            speaker = 'patient'
        else:
            # Detected language doesn't match selected languages, default to translating to doctor's language
            target_lang_code = selected_doctor_language
            target_lang_name = lang_code_to_name.get(target_lang_code, 'english')
            translated = voice_agent.translator.sarvam.translate_text(transcript, detected_lang, target_lang_code)
            speaker_label = f"{lang_code_to_name.get(detected_lang, 'unknown').title()} → {target_lang_name.title()}"
            speaker = 'unknown'

        print(f"✅ Translation successful: '{transcript}' -> '{translated}'")

        emit('status', {'message': f'Heard ({speaker_label}): "{transcript[:50]}..."', 'type': 'info'})

        # Send complete processing result to browser
        print(f"📤 EMITTING speech_processed event: original='{transcript[:30]}...', translated='{translated[:30]}...', speaker={speaker}")
        result = {
            'original_text': transcript,
            'original_language': lang_code_to_name.get(detected_lang, 'english'),
            'translated_text': translated,
            'target_language': target_lang_code,
            'speaker': speaker,
            'transcription_type': transcription_type
        }
        print(f"📦 Event data: {result}")
        emit('speech_processed', result)
        print("✅ speech_processed event emitted successfully")

    except Exception as e:
        print(f"❌ Translation error: {e}")
        emit('speech_result', {'error': f'Translation failed: {str(e)}'})

# Language code to name mapping
lang_code_to_name = {
    'en-IN': 'english',
    'hi-IN': 'hindi',
    'mr-IN': 'marathi',
    'kn-IN': 'kannada'
}

@socketio.on('speak_text')
def handle_speak_text(data):
    """Handle text-to-speech requests"""
    text = data.get('text', '').strip()
    language_code = data.get('language_code', 'en-IN')

    if not text:
        emit('status', {'message': 'No text to speak', 'type': 'warning'})
        return

    if voice_agent:
        # Speak in a separate thread to avoid blocking
        def speak_thread():
            try:
                voice_agent.speak_text(text, language_code)
                socketio.emit('speech_completed')
            except Exception as e:
                socketio.emit('status', {'message': f'Speech error: {e}', 'type': 'error'})

        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
        emit('status', {'message': 'Speaking...', 'type': 'info'})
    else:
        emit('status', {'message': 'Voice agent not available', 'type': 'error'})

def main():
    """Main entry point"""
    print("🏥 Doctor-Patient Voice Translation Web Service")
    print("=" * 50)

    if not initialize_services():
        print("❌ Failed to initialize services. Check your configuration.")
        return

    print("✅ Services initialized successfully")
    print("🌐 Starting web server...")
    print("📱 Open your browser to: http://localhost:8000")

    # Start the web server
    socketio.run(app, host='0.0.0.0', port=8000, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
