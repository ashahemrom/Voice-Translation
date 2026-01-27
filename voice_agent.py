#!/usr/bin/env python3
"""
Voice Translation Agent for Doctor-Patient Communication
Acts as an intermediary translator between doctor and patient
"""

import threading
import queue
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.spinner import Spinner

from sarvam_service import DoctorPatientTranslator, SarvamService, SarvamTranslationError

# Try to import voice libraries, provide fallbacks if not available
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Print warnings at module level
if not SPEECH_RECOGNITION_AVAILABLE:
    print("⚠️ Speech recognition not available - voice input disabled")

if not PYTTSX3_AVAILABLE:
    print("⚠️ Text-to-speech not available - voice output disabled")

class Speaker(Enum):
    """Enum for speaker identification"""
    DOCTOR = "doctor"
    PATIENT = "patient"
    UNKNOWN = "unknown"

class ConversationState(Enum):
    """Enum for conversation states"""
    WAITING_FOR_DOCTOR = "waiting_for_doctor"
    WAITING_FOR_PATIENT = "waiting_for_patient"
    TRANSLATING = "translating"
    SPEAKING = "speaking"
    ERROR = "error"

class VoiceTranslationAgent:
    """
    Voice Translation Agent that acts as an intermediary between doctor and patient.
    Handles real-time voice-to-voice translation with speaker detection.
    """

    def __init__(self, translator: DoctorPatientTranslator):
        self.translator = translator
        self.console = Console()

        # Audio components (with fallbacks)
        self.recognizer = None
        self.tts_engine = None

        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.console.print("[yellow]🎤 Speech recognition not available - using text input fallback[/yellow]")

        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self._configure_tts()
                self.console.print("[green]🔊 Text-to-speech initialized successfully[/green]")
            except Exception as e:
                self.console.print(f"[yellow]🔊 Text-to-speech failed to initialize: {e}[/yellow]")
                self.console.print("[yellow]🔊 Using text output only[/yellow]")
                self.tts_engine = None
        else:
            self.tts_engine = None
            self.console.print("[yellow]🔊 Text-to-speech not available - using text output only[/yellow]")

        # Conversation state
        self.current_speaker = Speaker.UNKNOWN
        self.conversation_state = ConversationState.WAITING_FOR_DOCTOR
        self.patient_language = "hindi"  # Default, can be changed

        # Audio queues and threading
        self.audio_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        self.speaking = False

        # Speaker detection (simplified - in production would use ML models)
        self.speaker_profiles = {
            Speaker.DOCTOR: {"voice_characteristics": "formal_medical"},
            Speaker.PATIENT: {"voice_characteristics": "casual_patient"}
        }

        # Callbacks for UI updates
        self.on_state_change: Optional[Callable] = None
        self.on_translation: Optional[Callable] = None
        self.on_speech_recognized: Optional[Callable] = None

    def _configure_tts(self):
        """Configure text-to-speech engine for better quality"""
        try:
            # Set voice properties
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a good voice for medical context
                for voice in voices:
                    if 'english' in voice.name.lower() and 'us' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break

            # Set speech rate (words per minute)
            self.tts_engine.setProperty('rate', 180)  # Slightly slower for clarity

            # Set volume
            self.tts_engine.setProperty('volume', 0.8)

        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not configure TTS: {e}[/yellow]")

    def set_patient_language(self, language: str):
        """Set the patient's preferred language"""
        self.patient_language = language.lower()
        self.console.print(f"[green]✓ Patient language set to: {language.title()}[/green]")

    def identify_speaker(self, audio_data) -> Speaker:
        """
        Identify the speaker based on audio characteristics.
        This is a simplified version - in production would use ML models.
        """
        # For now, we'll use a simple heuristic:
        # - If we're waiting for doctor, assume it's doctor
        # - If we're waiting for patient, assume it's patient
        # In production, this would analyze voice patterns, pitch, etc.

        if self.conversation_state == ConversationState.WAITING_FOR_DOCTOR:
            return Speaker.DOCTOR
        elif self.conversation_state == ConversationState.WAITING_FOR_PATIENT:
            return Speaker.PATIENT
        else:
            return Speaker.UNKNOWN

    def listen_for_speech(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for speech input and convert to text.
        Returns recognized text or None if no speech detected.
        Falls back to text input if speech recognition is not available.
        """
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer:
            # Fallback to text input
            self.console.print(f"[blue]📝 Text input mode (speech recognition not available)[/blue]")
            self.console.print("[dim]Type what you want to say, or press Enter for silence:[/dim]")
            try:
                text = input("> ").strip()
                return text if text else None
            except (EOFError, KeyboardInterrupt):
                return None

        try:
            with sr.Microphone() as source:
                self.console.print(f"[blue]🎤 Listening... (timeout: {timeout}s)[/blue]")

                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

                # Recognize speech
                text = self.recognizer.recognize_google(audio, language='en-IN')
                return text.strip()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            self.console.print("[yellow]❓ Could not understand audio[/yellow]")
            return None
        except sr.RequestError as e:
            self.console.print(f"[red]❌ Speech recognition error: {e}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]❌ Audio input error: {e}[/red]")
            return None

    def speak_text(self, text: str, language_code: str = "en-IN"):
        """
        Convert text to speech and play it.
        Falls back to text display if TTS is not available.
        """
        try:
            self.speaking = True
            self._update_state(ConversationState.SPEAKING)

            if not PYTTSX3_AVAILABLE or not self.tts_engine:
                # Fallback to text display
                self.console.print(f"[green]📢 Would speak: {text}[/green]")
                # Simulate speaking delay
                time.sleep(len(text) * 0.1)  # Rough estimate: 100ms per character
            else:
                # Configure voice based on language
                if language_code.startswith('hi'):  # Hindi
                    # For Hindi, we'd ideally use a Hindi TTS voice
                    # For now, we'll use the default voice
                    pass
                elif language_code.startswith('mr'):  # Marathi
                    pass
                elif language_code.startswith('kn'):  # Kannada
                    pass

                self.console.print(f"[green]🔊 Speaking: {text}[/green]")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()

        except Exception as e:
            self.console.print(f"[red]❌ Text-to-speech error: {e}[/red]")
            # Fallback to text display
            self.console.print(f"[green]📢 Would speak: {text}[/green]")
        finally:
            self.speaking = False

    def translate_and_speak(self, text: str, from_speaker: Speaker, to_speaker: Speaker):
        """
        Translate text and speak the translation.
        """
        try:
            self._update_state(ConversationState.TRANSLATING)

            if from_speaker == Speaker.DOCTOR and to_speaker == Speaker.PATIENT:
                # Doctor speaking to patient
                translated_text = self.translator.doctor_to_patient(text, self.patient_language)
                target_lang_code = self.translator.sarvam.get_language_code(self.patient_language)

            elif from_speaker == Speaker.PATIENT and to_speaker == Speaker.DOCTOR:
                # Patient speaking to doctor
                translated_text = self.translator.patient_to_doctor(text, self.patient_language)
                target_lang_code = "en-IN"  # Doctor speaks English

            else:
                raise ValueError(f"Unsupported speaker combination: {from_speaker} -> {to_speaker}")

            # Update UI with translation
            self._on_translation(text, translated_text, from_speaker, to_speaker)

            # Speak the translation
            self.speak_text(translated_text, target_lang_code)

            # Update conversation state
            if to_speaker == Speaker.DOCTOR:
                self._update_state(ConversationState.WAITING_FOR_DOCTOR)
            else:
                self._update_state(ConversationState.WAITING_FOR_PATIENT)

        except SarvamTranslationError as e:
            self.console.print(f"[red]❌ Translation failed: {e}[/red]")
            self._update_state(ConversationState.ERROR)
        except Exception as e:
            self.console.print(f"[red]❌ Translation error: {e}[/red]")
            self._update_state(ConversationState.ERROR)

    def process_conversation_turn(self):
        """
        Process one turn of the conversation.
        Listen for speech, identify speaker, translate, and respond.
        """
        try:
            # Listen for speech
            text = self.listen_for_speech(timeout=10)

            if not text:
                return False  # No speech detected

            # Notify UI about recognized speech
            self._on_speech_recognized(text)

            # Identify speaker
            speaker = self.identify_speaker(None)  # In production, pass audio data

            # Determine translation direction
            if speaker == Speaker.DOCTOR:
                target_speaker = Speaker.PATIENT
                self._update_state(ConversationState.WAITING_FOR_PATIENT)
            elif speaker == Speaker.PATIENT:
                target_speaker = Speaker.DOCTOR
                self._update_state(ConversationState.WAITING_FOR_DOCTOR)
            else:
                self.console.print("[yellow]⚠️ Could not identify speaker[/yellow]")
                return True

            # Translate and speak
            self.translate_and_speak(text, speaker, target_speaker)

            return True

        except KeyboardInterrupt:
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Conversation error: {e}[/red]")
            return True

    def start_conversation(self, external_control=False):
        """
        Start the voice-to-voice translation conversation.

        Args:
            external_control: If True, don't run internal loop (for web app control)
        """
        if not external_control:
            self.console.print(Panel.fit("🎯 Voice Translation Agent Started", style="bold green"))
            self.console.print("[dim]Press Ctrl+C to stop the conversation[/dim]\n")

        self._update_state(ConversationState.WAITING_FOR_DOCTOR)

        if not external_control:
            try:
                while True:
                    if not self.process_conversation_turn():
                        break

                    # Small delay between turns
                    time.sleep(1)

            except KeyboardInterrupt:
                self.console.print("\n[blue]⏹️ Conversation stopped by user[/blue]")
            except Exception as e:
                self.console.print(f"\n[red]❌ Conversation error: {e}[/red]")
            finally:
                self.cleanup()

    def process_single_turn(self):
        """
        Process a single conversation turn.
        Returns True if conversation should continue, False if it should stop.
        Used for external control (e.g., web app).
        """
        try:
            return self.process_conversation_turn()
        except Exception as e:
            self.console.print(f"[red]❌ Conversation turn error: {e}[/red]")
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            self.tts_engine.stop()
        except:
            pass

    def _update_state(self, new_state: ConversationState):
        """Update conversation state and notify listeners"""
        self.conversation_state = new_state
        if self.on_state_change:
            self.on_state_change(new_state)

    def _on_translation(self, original: str, translated: str, from_speaker: Speaker, to_speaker: Speaker):
        """Handle translation events"""
        if self.on_translation:
            self.on_translation(original, translated, from_speaker, to_speaker)

    def _on_speech_recognized(self, text: str):
        """Handle speech recognition events"""
        if self.on_speech_recognized:
            self.on_speech_recognized(text)

class VoiceInterface:
    """
    User interface for the voice translation agent with real-time updates.
    """

    def __init__(self, agent: VoiceTranslationAgent):
        self.agent = agent
        self.console = Console()
        self.live_display = None

        # Set up callbacks
        self.agent.on_state_change = self._on_state_change
        self.agent.on_translation = self._on_translation
        self.agent.on_speech_recognized = self._on_speech_recognized

    def _on_state_change(self, state: ConversationState):
        """Update UI when conversation state changes"""
        if self.live_display:
            self.live_display.update(self._create_status_panel())

    def _on_translation(self, original: str, translated: str, from_speaker: Speaker, to_speaker: Speaker):
        """Update UI when translation occurs"""
        self.console.print(f"\n[bold blue]{from_speaker.value.title()}:[/bold blue] {original}")
        self.console.print(f"[bold green]{to_speaker.value.title()}:[/bold green] {translated}")

    def _on_speech_recognized(self, text: str):
        """Update UI when speech is recognized"""
        pass  # Already handled in translation callback

    def _create_status_panel(self) -> Panel:
        """Create status panel showing current conversation state"""
        state_colors = {
            ConversationState.WAITING_FOR_DOCTOR: "blue",
            ConversationState.WAITING_FOR_PATIENT: "green",
            ConversationState.TRANSLATING: "yellow",
            ConversationState.SPEAKING: "cyan",
            ConversationState.ERROR: "red"
        }

        state_icons = {
            ConversationState.WAITING_FOR_DOCTOR: "👨‍⚕️",
            ConversationState.WAITING_FOR_PATIENT: "🧑",
            ConversationState.TRANSLATING: "🔄",
            ConversationState.SPEAKING: "🔊",
            ConversationState.ERROR: "❌"
        }

        color = state_colors.get(self.agent.conversation_state, "white")
        icon = state_icons.get(self.agent.conversation_state, "❓")

        status_text = f"{icon} {self.agent.conversation_state.value.replace('_', ' ').title()}"

        return Panel(
            f"[bold {color}]{status_text}[/bold {color}]\n\n"
            f"Patient Language: {self.agent.patient_language.title()}\n"
            f"Current Speaker: {self.agent.current_speaker.value.title()}",
            title="Voice Translation Agent",
            border_style=color
        )

    def start_interactive_session(self):
        """Start the interactive voice translation session"""
        # Language selection
        self.console.print("[bold cyan]Select Patient's Language:[/bold cyan]")
        languages = ["hindi", "marathi", "kannada"]

        for i, lang in enumerate(languages, 1):
            native_names = {"hindi": "हिंदी", "marathi": "मराठी", "kannada": "ಕನ್ನಡ"}
            self.console.print(f"{i}. {lang.title()} ({native_names[lang]})")

        while True:
            try:
                choice = int(input("\nEnter language number (1-3): "))
                if 1 <= choice <= 3:
                    selected_lang = languages[choice - 1]
                    self.agent.set_patient_language(selected_lang)
                    break
                else:
                    print("Please enter 1, 2, or 3.")
            except ValueError:
                print("Please enter a valid number.")

        # Instructions
        self.console.print("\n[bold yellow]🎯 Voice-to-Voice Translation Instructions:[/bold yellow]")
        self.console.print("• Speak clearly into your microphone")
        self.console.print("• Doctor speaks first (in English)")
        self.console.print("• Agent will translate and speak to patient")
        self.console.print("• Patient responds, agent translates back to doctor")
        self.console.print("• Press Ctrl+C to stop")

        # Start live display
        with Live(self._create_status_panel(), refresh_per_second=4) as live:
            self.live_display = live
            self.agent.start_conversation()
