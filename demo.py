#!/usr/bin/env python3
"""
Demo script for Doctor-Patient Voice Translation Service
Shows the system working with automatic interactions
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sarvam_service import SarvamService, DoctorPatientTranslator, SarvamTranslationError
from voice_agent import VoiceTranslationAgent, ConversationState
from config import SARVAM_API_KEY, LANGUAGE_CONFIG

def main():
    print("🎯 Doctor-Patient Translation Demo")
    print("=" * 40)

    # Check API key
    if not SARVAM_API_KEY or SARVAM_API_KEY == 'your_api_key_here':
        print("❌ API key not configured. Please set SARVAM_API_KEY in config.py")
        return

    try:
        # Initialize services
        print("🔧 Initializing translation service...")
        service = SarvamService()
        translator = DoctorPatientTranslator(service)
        voice_agent = VoiceTranslationAgent(translator)

        print("✅ Services initialized successfully")

        # Test basic translation
        print("\n🧪 Testing Translation Engine:")
        test_cases = [
            ("Hello, how are you?", "hindi"),
            ("Please describe your symptoms.", "marathi"),
            ("Take this medicine twice a day.", "kannada")
        ]

        for text, lang in test_cases:
            try:
                translated = translator.doctor_to_patient(text, lang)
                print(f"  ✓ {lang.title()}: '{text}' → '{translated}'")
            except Exception as e:
                print(f"  ❌ {lang.title()}: Error - {e}")

        # Demonstrate conversation flow
        print("\n💬 Simulating Doctor-Patient Conversation:")

        # Set patient language
        voice_agent.set_patient_language("hindi")
        print("🌐 Patient language: Hindi")

        # Simulate conversation turns
        conversation = [
            ("doctor", "Hello, how are you feeling today?"),
            ("patient", "मैं ठीक हूं, लेकिन सिरदर्द है"),
            ("doctor", "When did the headache start?"),
            ("patient", "कल शाम से शुरू हुआ")
        ]

        print("\n📝 Conversation Flow:")
        for speaker, message in conversation:
            if speaker == "doctor":
                print(f"👨‍⚕️ Doctor: {message}")
                translated = translator.doctor_to_patient(message, "hindi")
                print(f"   → Patient (Hindi): {translated}")
            else:
                print(f"🧑 Patient: {message}")
                translated = translator.patient_to_doctor(message, "hindi")
                print(f"   → Doctor (English): {translated}")
            print()

        print("🎉 Demo completed successfully!")
        print("\n🚀 To run the full application:")
        print("   python main.py")
        print("\n🎯 Choose option 1 for Text Translation")
        print("🎯 Choose option 2 for Voice Agent (with text fallbacks)")
        print("🎯 Choose option 3 for Web Interface (requires Flask-SocketIO)")

    except SarvamTranslationError as e:
        print(f"❌ Translation error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
