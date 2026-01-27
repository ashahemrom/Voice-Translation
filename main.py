#!/usr/bin/env python3
"""
Doctor-Patient Translation Service using Sarvam AI
Supports real-time translation between English (Doctor) and Hindi/Marathi/Kannada (Patients)
"""

import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.columns import Columns

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sarvam_service import SarvamService, DoctorPatientTranslator, SarvamTranslationError
from voice_agent import VoiceTranslationAgent, VoiceInterface
from config import SARVAM_API_KEY, LANGUAGE_CONFIG

# Initialize colorama for cross-platform colored output (with fallback)
try:
    from colorama import init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    print("⚠️ Colorama not available - using plain text output")

class DoctorPatientApp:
    """Interactive Doctor-Patient Translation Application"""

    def __init__(self):
        self.console = Console()
        self.sarvam_service = SarvamService()
        self.translator = DoctorPatientTranslator(self.sarvam_service)
        self.patient_language = None

    def show_welcome(self):
        """Display welcome message and setup"""
        welcome_text = Text("🏥 Doctor-Patient Translation Service", style="bold blue")
        welcome_text.append("\n\nUsing Sarvam AI for accurate Indic language translation", style="dim")
        welcome_text.append("\n\n✨ Features:", style="bold cyan")
        welcome_text.append("\n• Text Translation (Interactive)", style="dim")
        welcome_text.append("\n• Voice-to-Voice Translation (Real-time)", style="dim")

        panel = Panel(welcome_text, title="Welcome", border_style="blue")
        self.console.print(panel)

        # Check API key
        if SARVAM_API_KEY == 'your_api_key_here':
            self.console.print("\n[red]⚠️  Warning: API key not configured![/red]")
            self.console.print("Please set your SARVAM_API_KEY in the environment or config.py")
            self.console.print("Get your API key from: https://dashboard.sarvam.ai/")
            return False
        return True

    def select_patient_language(self):
        """Let user select the patient's preferred language"""
        self.console.print("\n[bold cyan]Select Patient's Language:[/bold cyan]")

        languages = self.translator.get_supported_patient_languages()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Language", style="white")
        table.add_column("Native Name", style="yellow")

        language_names = {
            'hindi': 'हिंदी (Hindi)',
            'marathi': 'मराठी (Marathi)',
            'kannada': 'ಕನ್ನಡ (Kannada)'
        }

        for i, lang in enumerate(languages, 1):
            table.add_row(str(i), lang.title(), language_names.get(lang, lang))

        self.console.print(table)

        while True:
            choice = Prompt.ask("\nEnter language number (1-3)", default="1")
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(languages):
                    self.patient_language = languages[choice_idx]
                    self.console.print(f"\n[green]✓ Selected: {self.patient_language.title()}[/green]")
                    break
                else:
                    self.console.print("[red]Invalid choice. Please select 1-3.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")

    def show_translation_demo(self):
        """Show sample translations to demonstrate functionality"""
        self.console.print("\n[bold green]📝 Translation Demo:[/bold green]")

        sample_texts = [
            "Hello, how are you feeling today?",
            "Please describe your symptoms.",
            "Take this medicine twice a day.",
            "When did the pain start?"
        ]

        for text in sample_texts:
            try:
                translated = self.translator.doctor_to_patient(text, self.patient_language)
                self.console.print(f"[blue]Doctor:[/blue] {text}")
                self.console.print(f"[green]Patient ({self.patient_language.title()}):[/green] {translated}")
                self.console.print()
            except SarvamTranslationError as e:
                self.console.print(f"[red]Translation error: {e}[/red]")
                break

    def interactive_translation(self):
        """Interactive translation mode"""
        self.console.print("\n[bold yellow]🎯 Interactive Translation Mode[/bold yellow]")
        self.console.print("Type 'quit' to exit, 'switch' to change language, 'demo' for examples")

        while True:
            # Doctor's input (English)
            doctor_input = Prompt.ask("\n[blue]Doctor (English)[/blue]").strip()

            if doctor_input.lower() == 'quit':
                break
            elif doctor_input.lower() == 'switch':
                self.select_patient_language()
                continue
            elif doctor_input.lower() == 'demo':
                self.show_translation_demo()
                continue
            elif not doctor_input:
                continue

            try:
                # Translate to patient's language
                patient_translation = self.translator.doctor_to_patient(doctor_input, self.patient_language)

                # Display translation
                self.console.print(f"[green]→ Patient ({self.patient_language.title()}):[/green] {patient_translation}")

                # Simulate patient's response (you would get this from voice input in real app)
                patient_response = Prompt.ask(f"\n[green]Patient's response ({self.patient_language.title()})[/green]").strip()

                if patient_response:
                    # Translate patient's response back to English for doctor
                    doctor_translation = self.translator.patient_to_doctor(patient_response, self.patient_language)
                    self.console.print(f"[blue]→ Doctor (English):[/blue] {doctor_translation}")

            except SarvamTranslationError as e:
                self.console.print(f"[red]❌ Translation Error: {e}[/red]")
                self.console.print("[yellow]💡 Tip: Check your internet connection and API key[/yellow]")

    def select_mode(self):
        """Let user select between text and voice translation"""
        self.console.print("\n[bold cyan]Choose Translation Mode:[/bold cyan]")
        self.console.print("1. 📝 Text Translation (Interactive chat)")
        self.console.print("2. 🎤 Voice-to-Voice Translation (Real-time agent)")
        self.console.print("3. 🌐 Web Interface (Browser-based UI)")
        self.console.print("4. 🚪 Exit")

        while True:
            choice = Prompt.ask("\nEnter your choice (1-4)", default="1")
            if choice == "1":
                return "text"
            elif choice == "2":
                return "voice"
            elif choice == "3":
                return "web"
            elif choice == "4":
                return "exit"
            else:
                self.console.print("[red]Please enter 1, 2, 3, or 4.[/red]")

    def start_voice_translation(self):
        """Start the voice-to-voice translation agent"""
        try:
            # Initialize voice agent
            voice_agent = VoiceTranslationAgent(self.translator)
            voice_interface = VoiceInterface(voice_agent)

            # Start the voice interface
            voice_interface.start_interactive_session()

        except ImportError as e:
            self.console.print(f"[red]❌ Voice features require additional setup: {e}[/red]")
            self.console.print("[yellow]Please install missing dependencies and try again.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]❌ Voice translation error: {e}[/red]")

    def start_web_interface(self):
        """Start the web interface"""
        try:
            self.console.print("[bold green]🌐 Starting Web Interface...[/bold green]")
            self.console.print("[dim]This will open a web server at http://localhost:5000[/dim]")
            self.console.print("[yellow]Press Ctrl+C to stop the web server[/yellow]")

            # Import and run web app
            import subprocess
            import sys
            import os

            # Run web_app.py as subprocess
            web_app_path = os.path.join(os.path.dirname(__file__), 'web_app.py')
            process = subprocess.Popen([sys.executable, web_app_path])

            try:
                process.wait()
            except KeyboardInterrupt:
                self.console.print("\n[blue]⏹️ Stopping web server...[/blue]")
                process.terminate()
                process.wait()

        except Exception as e:
            self.console.print(f"[red]❌ Web interface error: {e}[/red]")

    def run(self):
        """Main application loop"""
        if not self.show_welcome():
            return

        while True:
            mode = self.select_mode()

            if mode == "exit":
                break
            elif mode == "text":
                # Text translation mode
                self.select_patient_language()
                self.show_translation_demo()

                if Confirm.ask("\nWould you like to try interactive text translation?", default=True):
                    self.interactive_translation()
            elif mode == "voice":
                # Voice translation mode
                self.start_voice_translation()
            elif mode == "web":
                # Web interface mode
                self.start_web_interface()

            if not Confirm.ask("\nWould you like to try another mode?", default=False):
                break

        self.console.print("\n[bold blue]Thank you for using Doctor-Patient Translation Service![/bold blue]")
        self.console.print("[dim]Built with Sarvam AI for better healthcare communication[/dim]")

def main():
    """Main entry point"""
    try:
        app = DoctorPatientApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()
