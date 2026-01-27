# 🏥 Doctor-Patient Translation Service

A real-time translation service for doctor-patient communication using **Sarvam AI**, supporting English, Hindi, Marathi, and Kannada languages.

## ✨ Features

- **Real-time Translation**: Instant translation between doctor (English) and patient (Hindi/Marathi/Kannada)
- **Voice-to-Voice Agent**: Live intermediary translator that recognizes speakers and translates conversations
- **Web Interface**: Modern browser-based UI with real-time capabilities
- **Sarvam AI Integration**: Uses state-of-the-art Indic language translation
- **Interactive Interface**: User-friendly command-line interface with Rich formatting
- **Speaker Recognition**: Automatically detects doctor vs patient speech
- **Text Fallbacks**: Works with text input when voice features unavailable
- **Real-time Communication**: WebSocket-based live updates
- **Error Handling**: Robust error handling with helpful messages
- **Extensible**: Easy to add more languages and features

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Sarvam AI API Key

1. Visit [Sarvam AI Dashboard](https://dashboard.sarvam.ai/)
2. Sign up and get your API key
3. Set your API key in `config.py`:
   ```python
   SARVAM_API_KEY = "your_actual_api_key_here"
   ```

### 3. Run the Application

```bash
python main.py
```

## 🌐 Web Interface

The service includes a modern web-based interface with real-time capabilities:

### Features
- **Live Voice Translation**: Real-time voice-to-voice translation in the browser
- **Language Selection**: Easy language switching with visual indicators
- **Text Translation**: Manual text translation with instant results
- **Conversation Log**: Complete conversation history with timestamps
- **Status Indicators**: Real-time status updates and system messages
- **Responsive Design**: Works on desktop and mobile devices
- **WebSocket Communication**: Instant updates without page refresh

### Accessing the Web Interface

```bash
python main.py
# Choose option 3: "🌐 Web Interface (Browser-based UI)"
```

The web server will start at `http://localhost:5000`. Open this URL in your browser.

### Web Demo
If you can't install Flask dependencies, you can view a static demo of the web interface:

```bash
open web_demo.html  # On macOS
# or
# Open web_demo.html in your browser
```

The demo shows the full interface design and functionality preview.

### Web Interface Sections

#### Language Selection
- Choose between Hindi, Marathi, and Kannada for patient communication
- Visual language buttons with native script display

#### Voice Translation Agent
- Start/stop voice conversations
- Real-time status indicators (listening/speaking/ready)
- Automatic speaker detection and turn management

#### Text Translation
- Tabbed interface for Doctor→Patient and Patient→Doctor translation
- Manual text input with instant translation
- Text-to-speech capabilities for both languages

#### Conversation Log
- Complete history of all translations and interactions
- Color-coded entries (Doctor/Patient/System)
- Clear log functionality

## 🎤 Voice-to-Voice Translation Agent

The service includes an advanced **Voice Translation Agent** that acts as a live intermediary translator:

### How It Works
1. **Speaker Recognition**: Automatically detects whether the doctor or patient is speaking
2. **Speech-to-Text**: Converts speech to text (with Google Speech Recognition)
3. **Translation**: Translates using Sarvam AI's high-quality Indic language models
4. **Text-to-Speech**: Speaks the translation aloud (with pyttsx3)
5. **Conversation Flow**: Manages turn-taking between doctor and patient

### Example Conversation Flow
```
Doctor speaks: "Hello, how are you feeling today?"
→ Agent recognizes doctor, translates to Hindi
→ Agent speaks: "नमस्ते, आज आप कैसी महसूस कर रहे हैं?"

Patient responds: "मैं ठीक हूं, लेकिन सिरदर्द है"
→ Agent recognizes patient, translates to English
→ Agent speaks: "I am fine but yes, I have a headache"

Doctor asks: "When did the headache start?"
→ Agent recognizes doctor, translates to Hindi
→ Agent speaks: "सिरदर्द कब शुरू हुआ?"
```

### Voice Mode Features
- **Real-time Processing**: Instant translation with minimal delay
- **Fallback Support**: Works with text input when microphone unavailable
- **State Management**: Tracks conversation flow and speaker turns
- **Multi-language**: Supports Hindi, Marathi, and Kannada patients
- **Error Recovery**: Graceful handling of recognition/translation failures

## 📋 Supported Languages

| Language | Code | Usage |
|----------|------|-------|
| English | `en-IN` | Doctor's language |
| Hindi | `hi-IN` | Patient language |
| Marathi | `mr-IN` | Patient language |
| Kannada | `kn-IN` | Patient language |

## 🎯 Usage Examples

### Interactive Mode
```
🏥 Doctor-Patient Translation Service

Select Patient's Language:
┌─────────┬──────────┬─────────────────┐
│ Option  │ Language │ Native Name     │
├─────────┼──────────┼─────────────────┤
│ 1       │ Hindi    │ हिंदी (Hindi)    │
│ 2       │ Marathi  │ मराठी (Marathi)  │
│ 3       │ Kannada  │ ಕನ್ನಡ (Kannada)  │
└─────────┴──────────┴─────────────────┘

Enter language number (1-3): 1

📝 Translation Demo:
Doctor: Hello, how are you feeling today?
Patient (Hindi): नमस्ते, आज आप कैसे महसूस कर रहे हैं?

🎯 Interactive Translation Mode
Doctor (English): Please describe your symptoms.
→ Patient (Hindi): कृपया अपने लक्षणों का वर्णन करें।
```

### Commands
- `quit` - Exit the application
- `switch` - Change patient language
- `demo` - Show translation examples

## 🛠️ API Integration

### Basic Usage

```python
from sarvam_service import SarvamService, DoctorPatientTranslator

# Initialize service
service = SarvamService()
translator = DoctorPatientTranslator(service)

# Translate doctor to patient
patient_text = translator.doctor_to_patient("Hello, how are you?", "hindi")
print(patient_text)  # नमस्ते, आप कैसे हैं?

# Translate patient to doctor
doctor_text = translator.patient_to_doctor("मैं ठीक हूं", "hindi")
print(doctor_text)  # I am fine
```

### Direct API Usage

```python
from sarvam_service import SarvamService

service = SarvamService()

# Translate between any supported languages
result = service.translate_text("Hello world", "en-IN", "hi-IN")
print(result)  # हैलो वर्ल्ड
```

## 📁 Project Structure

```
├── main.py                 # Main application interface
├── sarvam_service.py       # Sarvam AI integration and translation logic
├── voice_agent.py          # Voice translation agent with speaker recognition
├── web_app.py             # Flask web application with SocketIO
├── config.py              # Configuration and settings
├── requirements.txt       # Python dependencies
├── test_sarvam.py         # Unit tests
├── setup.py               # Setup automation script
├── templates/
│   └── index.html         # Web interface template
├── static/
│   ├── css/
│   │   └── styles.css     # Web interface styles
│   └── js/
│       └── app.js         # Frontend JavaScript
└── README.md              # This file
```

## 🔧 Configuration

Edit `config.py` to customize:

- API key
- Supported languages
- Translation pairs
- API endpoints

## 🚨 Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure your Sarvam AI API key is correctly set in `config.py`
   - Verify the key is active and has credits

2. **Network Errors**
   - Check your internet connection
   - Ensure firewall allows HTTPS requests

3. **Translation Errors**
   - Verify the language pair is supported
   - Check that input text is not empty

### Error Messages

- `"API request failed"` - Check API key and network connection
- `"Translation from X to Y is not supported"` - Verify language codes
- `"Network error"` - Check internet connection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **Sarvam AI** for providing excellent Indic language translation
- Built for improving healthcare communication in multilingual India

---

**Made with ❤️ for better doctor-patient communication**
