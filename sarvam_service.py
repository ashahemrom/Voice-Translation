import requests
from typing import Optional, Dict, Any
import json
import re
import base64
from config import SARVAM_API_KEY, SARVAM_BASE_URL, LANGUAGE_CONFIG, SUPPORTED_TRANSLATIONS

class SarvamTranslationError(Exception):
    """Custom exception for Sarvam AI translation errors"""
    pass

class SarvamService:
    """Sarvam AI Translation Service for Doctor-Patient Communication"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or SARVAM_API_KEY
        self.base_url = SARVAM_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'API-Subscription-Key': self.api_key
        })

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Sarvam AI API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data, timeout=30)

            if response.status_code != 200:
                raise SarvamTranslationError(f"API request failed: {response.status_code} - {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise SarvamTranslationError(f"Network error: {str(e)}")

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text using Azure OpenAI

        Args:
            text: Text to analyze

        Returns:
            Detected language code (e.g., 'en-IN', 'hi-IN')
        """
        if not text.strip():
            return 'en-IN'  # Default to English for empty text

        try:
            # Try Azure OpenAI language detection first
            return self._azure_language_detection(text)
        except Exception as e:
            print(f"Azure OpenAI language detection failed: {e}")
            # Fallback to pattern-based detection
            return self._fallback_language_detection(text)

    def _azure_language_detection(self, text: str) -> str:
        """
        Use direct HTTP requests to Azure OpenAI (simplest approach)
        """
        try:
            return self._azure_http_detection(text)
        except Exception as e:
            raise Exception(f"Azure OpenAI HTTP request failed: {e}")

    def _azure_http_detection(self, text: str) -> str:
        """
        Fallback: Direct HTTP request to Azure OpenAI (bypasses client issues)
        """
        import requests
        import json

        # Use the exact URL format provided by the user
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
            "temperature": 0.1
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

    def _fallback_language_detection(self, text: str) -> str:
        """
        Improved fallback language detection when API is not available
        """
        # Check for Devanagari script (Hindi)
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi-IN'  # Contains Devanagari script = definitely Hindi

        # English indicators
        english_words = [
            'hello', 'hi', 'good', 'morning', 'afternoon', 'evening', 'please', 'thank', 'you',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would',
            'take', 'medicine', 'prescription', 'diagnosis', 'treatment', 'check', 'blood',
            'pressure', 'temperature', 'fever', 'cough', 'pain', 'headache', 'stomach', 'chest'
        ]

        # Hindi/romanized Hindi + Marathi indicators (expanded list)
        hindi_words = [
            # Original Hindi words
            'hai', 'hain', 'nahi', 'nahin', 'nahi', 'main', 'hum', 'tum', 'aap', 'kya', 'kyon', 'kaise', 'kahan',
            'yeh', 'yah', 'woh', 'aur', 'par', 'lekin', 'magar', 'ki', 'ka', 'ke', 'ko', 'se', 'mein', 'pe',
            'tak', 'kar', 'raha', 'rahi', 'rahe', 'tha', 'thi', 'the', 'hoga', 'hog', 'hun', 'hoon',
            'bhai', 'bahut', 'sahi', 'theek', 'ab', 'ulta', 'kam', 'karta', 'karti', 'samajh', 'samjho',
            'dard', 'dukh', 'bimari', 'doctor', 'hospital', 'tablet', 'syrup', 'mujhe', 'muje', 'mujhko',
            'tera', 'tera', 'teri', 'teri', 'apna', 'apni', 'apne', 'apno', 'yahin', 'wahin', 'idhar', 'udhar',
            'upar', 'neeche', ' andar', 'bahar', 'samne', 'peeche', 'bina', 'sath', 'ke', 'saath',
            'padega', 'padegi', 'padenge', 'karna', 'karne', 'karni', 'karu', 'kare', 'karega', 'karegi',
            'jao', 'jaoge', 'gaya', 'gayi', 'rahta', 'rahti', 'rahte', 'soch', 'sochta', 'sochte',
            'khao', 'khaoge', 'khana', 'khane', 'peena', 'peene', 'peo', 'piyo', 'lete', 'lena', 'deta', 'deti',

            # Marathi romanized words (what browser transcribes)
            'marathi', 'mala', 'kamyat', 'kami', 'zyada', 'thoda', 'acha', 'kharab', 'barobar', 'chalel',
            'nahi', 'ho', 'naahi', 'nko', 'pn', 'te', 'hi', 'mi', 'tu', 'to', 'ti', 'te', 'amhi', 'tumhi',
            'apn', 'majha', 'tujha', 'tyacha', 'tichya', 'amchya', 'tumchya', 'aplya', 'konala', 'kyala',
            'kay', 'kiti', 'kuth', 'kasa', 'kala', 'kela', 'karta', 'yeil', 'ala', 'jata', 'basla', 'rahila',
            'padla', 'khalla', 'pilala', 'dela', 'ghyala', 'anla', 'sodla', 'bolala', 'aikala', 'pathavala',
            'doctor', 'hospital', 'medicine', 'tablet', 'injection', 'checkup', 'blood', 'sugar', 'bp',
            'pain', 'fever', 'cold', 'cough', 'headache', 'stomach', 'throat', 'ear', 'eye', 'nose',
            'dava', 'injection', 'xray', 'sonography', 'bloodtest', 'urine', 'stool', 'ecg', 'echo'
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
                return 'en-IN'  # Default to English, not Hindi

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text between languages

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en-IN')
            target_lang: Target language code (e.g., 'hi-IN')

        Returns:
            Translated text
        """
        if (source_lang, target_lang) not in SUPPORTED_TRANSLATIONS:
            raise SarvamTranslationError(f"Translation from {source_lang} to {target_lang} is not supported")

        if not text.strip():
            return ""

        # Based on the Laravel package, the API structure appears to be:
        # POST to translation endpoint with source_language, target_language, and input
        data = {
            "source_language_code": source_lang,
            "target_language_code": target_lang,
            "speaker_gender": "Male",  # Optional, can be customized
            "mode": "formal",  # Optional, can be customized
            "model": "mayura:v1",  # Based on common patterns
            "input": text
        }

        try:
            # The exact endpoint might be /translate or /text/translate
            # Let's try the most common pattern
            result = self._make_request("/translate", data)

            # Extract translated text from response
            # Based on common API patterns, it should be in 'translated_text' or similar
            if 'translated_text' in result:
                return result['translated_text']
            elif 'output' in result:
                return result['output']
            elif 'text' in result:
                return result['text']
            else:
                # If we can't find the expected field, return the raw response for debugging
                return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            raise SarvamTranslationError(f"Translation failed: {str(e)}")

    def get_language_code(self, language_name: str) -> str:
        """Get language code from language name"""
        language_name = language_name.lower().strip()
        return LANGUAGE_CONFIG.get(language_name, language_name)

    def validate_languages(self, source: str, target: str) -> tuple[str, str]:
        """Validate and normalize language codes"""
        source_code = self.get_language_code(source)
        target_code = self.get_language_code(target)

        if source_code not in [lang for langs in LANGUAGE_CONFIG.values() for lang in [langs]]:
            raise SarvamTranslationError(f"Unsupported source language: {source}")

        if target_code not in [lang for langs in LANGUAGE_CONFIG.values() for lang in [langs]]:
            raise SarvamTranslationError(f"Unsupported target language: {target}")

        return source_code, target_code

    def text_to_speech(self, text: str, language: str, speaker_gender: str = "Male") -> bytes:
        """
        Convert text to speech using Sarvam AI TTS

        Args:
            text: Text to convert to speech
            language: Target language code (e.g., 'en-IN', 'hi-IN')
            speaker_gender: Speaker gender ('Male' or 'Female')

        Returns:
            Audio data as bytes
        """
        try:
            # Map language codes to Sarvam TTS format
            language_map = {
                'en-IN': 'english',
                'hi-IN': 'hindi',
                'mr-IN': 'marathi',
                'kn-IN': 'kannada'
            }

            tts_language = language_map.get(language, 'english')

            endpoint = "/speech"
            data = {
                "inputs": [text],
                "target_language_code": tts_language,
                "speaker_gender": speaker_gender,
                "pace": 1.0
            }

            response = self._make_request(endpoint, data)

            if "audios" in response and len(response["audios"]) > 0:
                # Decode base64 audio data
                import base64
                audio_b64 = response["audios"][0]
                audio_data = base64.b64decode(audio_b64)
                return audio_data
            else:
                raise SarvamTranslationError("No audio data received from TTS API")

        except Exception as e:
            raise SarvamTranslationError(f"TTS failed: {str(e)}")

    def speech_to_text(self, audio_data: bytes, language: str = None) -> str:
        """
        Convert speech audio to text using Sarvam AI STT

        Args:
            audio_data: Audio file data as bytes
            language: Optional language code hint (e.g., 'hi-IN', 'mr-IN')

        Returns:
            Transcribed text
        """
        try:
            print(f"🎤 STT request: {len(audio_data)} bytes, language: {language}")

            # Sarvam expects multipart/form-data with a file
            import io

            # Create a file-like object from the audio data
            audio_file = io.BytesIO(audio_data)
            audio_file.name = 'audio.webm'  # Give it a filename

            # Prepare form data
            files = {
                'file': ('audio.webm', audio_file, 'audio/webm')
            }

            data = {
                'model': 'saarika:v1'
            }

            # Add language hint if provided
            if language:
                # Map to Sarvam's language format
                lang_map = {
                    'en-IN': 'english',
                    'hi-IN': 'hindi',
                    'mr-IN': 'marathi',
                    'kn-IN': 'kannada'
                }
                sarvam_lang = lang_map.get(language, 'hindi')
                data["language"] = sarvam_lang

            # Make multipart request instead of JSON
            url = f"{self.base_url}/speech-to-text"
            print(f"📡 Making multipart STT request to: {url}")

            response = self.session.post(url, files=files, data=data, timeout=30)

            if response.status_code != 200:
                raise SarvamTranslationError(f"API request failed: {response.status_code} - {response.text}")

            response_data = response.json()
            print(f"📥 STT response: {response_data}")

            if "transcript" in response_data:
                transcript = response_data["transcript"]
                print(f"✅ STT transcript: '{transcript}'")
                return transcript
            else:
                raise SarvamTranslationError("No transcript in STT response")

        except Exception as e:
            print(f"❌ STT failed: {e}")
            raise SarvamTranslationError(f"Speech-to-text failed: {str(e)}")

    def speech_to_text_with_language(self, audio_data: bytes) -> tuple[str, str]:
        """
        Convert speech to text and detect language using Sarvam AI

        Args:
            audio_data: Audio file data as bytes

        Returns:
            Tuple of (transcribed_text, detected_language_code)
        """
        try:
            print(f"🎤 STT + Language detection request: {len(audio_data)} bytes")

            # Sarvam expects multipart/form-data with a file
            import io

            # Create a file-like object from the audio data
            audio_file = io.BytesIO(audio_data)
            audio_file.name = 'audio.webm'  # Give it a filename

            # Prepare form data
            files = {
                'file': ('audio.webm', audio_file, 'audio/webm')
            }

            data = {
                'model': 'saarika:v1'
            }

            # Make multipart request instead of JSON
            url = f"{self.base_url}/speech-to-text"
            print(f"📡 Making multipart STT+Lang request to: {url}")
            print(f"📦 Files: {files}")
            print(f"📋 Data: {data}")

            response = self.session.post(url, files=files, data=data, timeout=30)
            print(f"📊 Response status: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")

            if response.status_code != 200:
                raise SarvamTranslationError(f"API request failed: {response.status_code} - {response.text}")

            response_data = response.json()
            print(f"📥 STT+Lang response: {response_data}")

            transcript = response_data.get("transcript", "")
            detected_lang = response_data.get("language", "english")

            # Map back to our language codes
            lang_reverse_map = {
                'english': 'en-IN',
                'hindi': 'hi-IN',
                'marathi': 'mr-IN',
                'kannada': 'kn-IN'
            }

            language_code = lang_reverse_map.get(detected_lang, 'hi-IN')

            print(f"✅ STT result: '{transcript}' in {language_code}")
            return transcript, language_code

        except Exception as e:
            print(f"❌ STT+Language failed: {e}")
            raise SarvamTranslationError(f"Speech-to-text with language detection failed: {str(e)}")

    def text_to_speech_url(self, text: str, language: str, speaker_gender: str = "Male") -> str:
        """
        Get TTS audio URL for direct browser playback

        Args:
            text: Text to convert to speech
            language: Target language code
            speaker_gender: Speaker gender

        Returns:
            URL to audio file
        """
        try:
            print(f"🔊 TTS API call: text='{text}', language='{language}', gender='{speaker_gender}'")

            # Map language codes to Sarvam TTS format
            language_map = {
                'en-IN': 'english',
                'hi-IN': 'hindi',
                'mr-IN': 'marathi',
                'kn-IN': 'kannada'
            }

            tts_language = language_map.get(language, 'english')
            print(f"🌐 Mapped language: {language} -> {tts_language}")

            endpoint = "/speech"
            data = {
                "inputs": [text],
                "target_language_code": tts_language,
                "speaker_gender": speaker_gender,
                "pace": 1.0
            }

            print(f"📡 Making TTS API request to: {endpoint}")
            print(f"📦 Request data: {data}")

            response = self._make_request(endpoint, data)
            print(f"📥 TTS API response: {response}")

            if "audio_url" in response:
                print(f"✅ Found audio_url in response")
                return response["audio_url"]
            elif "audios" in response and len(response["audios"]) > 0:
                print(f"✅ Found base64 audio data in response")
                # If we get base64 data, we need to serve it from our server
                # For now, return a data URL
                import base64
                audio_b64 = response["audios"][0]
                audio_url = f"data:audio/wav;base64,{audio_b64}"
                return audio_url
            else:
                print(f"❌ No audio data in response: {response}")
                raise SarvamTranslationError("No audio URL or data received from TTS API")

        except Exception as e:
            print(f"💥 TTS API call failed: {e}")
            raise SarvamTranslationError(f"TTS URL generation failed: {str(e)}")

class DoctorPatientTranslator:
    """Specialized translator for doctor-patient communication"""

    def __init__(self, sarvam_service: SarvamService):
        self.sarvam = sarvam_service
        self.doctor_lang = LANGUAGE_CONFIG['english']  # Doctor speaks English

    def doctor_to_patient(self, text: str, patient_language: str) -> str:
        """Translate doctor's English to patient's language"""
        patient_lang_code = self.get_language_code(patient_language)
        return self.sarvam.translate_text(text, self.doctor_lang, patient_lang_code)

    def patient_to_doctor(self, text: str, patient_language: str) -> str:
        """Translate patient's language to doctor's English"""
        patient_lang_code = self.get_language_code(patient_language)
        return self.sarvam.translate_text(text, patient_lang_code, self.doctor_lang)

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        return self.sarvam.detect_language(text)

    def get_language_code(self, language_name: str) -> str:
        """Get language code from patient language name"""
        return self.sarvam.get_language_code(language_name)

    def get_supported_patient_languages(self) -> list[str]:
        """Get list of supported patient languages (excluding English)"""
        return [lang for lang in LANGUAGE_CONFIG.keys() if lang != 'english']
