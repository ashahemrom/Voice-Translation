// Simple Voice Translator - Frontend JavaScript

class VoiceTranslator {
    constructor() {
        this.socket = null;
        this.isListening = false;
        this.currentSpeaker = null; // 'doctor' or 'patient'
        this.recognition = null;
        this.init();
    }

    async init() {
        this.connectSocket();
        this.bindEvents();
        await this.initAudioRecording();
        this.updateStatus('🎤 Ready to start listening');
    }

    connectSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to voice translator');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from voice translator');
        });

        this.socket.on('status', (data) => {
            this.showMessage(data.message, data.type);
        });

        this.socket.on('speech_processed', (data) => {
            this.handleProcessedSpeech(data);
        });
    }

    bindEvents() {
        const startStopBtn = document.getElementById('start-stop-btn');
        if (startStopBtn) {
            startStopBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleListening();
            });
        }

        // Bind speak buttons
        const speakAsDoctorBtn = document.getElementById('speak-as-doctor');
        const speakAsPatientBtn = document.getElementById('speak-as-patient');

        if (speakAsDoctorBtn) {
            speakAsDoctorBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSpeakButton('doctor');
            });
        }

        if (speakAsPatientBtn) {
            speakAsPatientBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSpeakButton('patient');
            });
        }
    }

    async initAudioRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showMessage('❌ Browser does not support audio recording', 'error');
            return;
        }

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            this.mediaStream = stream;
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                // Convert audio chunks to base64 and send to server
                this.processRecordedAudio();
            };

            console.log('🎤 Audio recording initialized successfully');

        } catch (error) {
            console.error('Audio recording initialization failed:', error);
            this.showMessage('❌ Microphone access denied or not available', 'error');
        }
    }

    async processRecordedAudio() {
        if (this.audioChunks.length === 0) {
            this.showMessage('⚠️ No audio recorded', 'warning');
            return;
        }

        try {
            // Combine audio chunks into a single blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

            // Convert blob to base64
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix

                console.log(`📤 Sending ${base64Audio.length} chars of audio data to server`);

                // Send audio data to server for Sarvam STT processing
                this.socket.emit('audio_data', {
                    audio: base64Audio,
                    speaker: this.currentSpeaker
                });

                this.updateStatus('🔄 Processing speech...');
            };

            reader.readAsDataURL(audioBlob);

        } catch (error) {
            console.error('Audio processing error:', error);
            this.showMessage('❌ Audio processing failed', 'error');
        }

        // Clear audio chunks for next recording
        this.audioChunks = [];
    }

    handleSpeakButton(speaker) {
        if (this.isListening && this.currentSpeaker === speaker) {
            // Stop recording if already recording this speaker
            this.stopListening();
        } else {
            // Start recording for this speaker
            if (this.isListening) {
                // Stop any current recording first
                this.stopListening();
            }
            this.startListeningForSpeaker(speaker);
        }
    }

    startListeningForSpeaker(speaker) {
        this.currentSpeaker = speaker;
        this.startListening();
    }

    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    startListening() {
        if (this.mediaRecorder && !this.isListening) {
            try {
                this.isListening = true;
                this.audioChunks = []; // Clear any previous chunks
                this.mediaRecorder.start();
                this.updateStatus('🎤 Recording...');
                this.updateButtonState(true);

                // Auto-stop after 3 seconds for demo purposes
                setTimeout(() => {
                    if (this.isListening) {
                        this.stopListening();
                    }
                }, 3000);

            } catch (error) {
                console.error('Error starting recording:', error);
                this.showMessage('❌ Failed to start recording', 'error');
                this.isListening = false;
                this.updateButtonState(false);
            }
        } else if (!this.mediaRecorder) {
            this.showMessage('❌ Audio recording not initialized', 'error');
        }
    }

    stopListening() {
        if (this.mediaRecorder && this.isListening) {
            this.isListening = false;
            this.mediaRecorder.stop();
            this.updateStatus('⏹️ Processing...');
            this.updateButtonState(false);
        }
    }

    // Removed handleSpeechResult - now using direct audio recording to server


    handleProcessedSpeech(data) {
        console.log('🎯 RECEIVED speech_processed event from server!');
        console.log('📦 Raw event data:', data);
        const transcriptionType = data.transcription_type || '🎭 MOCK';
        console.log(`${transcriptionType} transcription received`);
        const originalText = data.original_text;
        const originalLanguage = data.original_language; // 'english', 'hindi', 'marathi', or 'kannada'
        const translatedText = data.translated_text;
        const targetLanguage = data.target_language; // 'en-IN', 'hi-IN', 'mr-IN', or 'kn-IN'
        const speaker = data.speaker; // 'doctor' or 'patient'

        console.log('📝 Adding original text:', originalText, 'to speaker:', speaker);
        // Add original text to the speaker's column
        if (speaker === 'doctor') {
            this.addMessageToChat(originalText, 'doctor', 'original');
        } else {
            this.addMessageToChat(originalText, 'patient', 'original');
        }

        console.log('📝 Adding translation:', translatedText, 'to other speaker');
        // Add translation to the other column
        if (speaker === 'doctor') {
            this.addMessageToChat(translatedText, 'patient', 'translation');
        } else {
            this.addMessageToChat(translatedText, 'doctor', 'translation');
        }

        // Speak the translation - try Sarvam TTS first, fallback to browser TTS
        console.log('🔊 Speaking translation:', translatedText);
        console.log('🌐 Target language for speech:', targetLanguage);

        // For now, skip Sarvam TTS and use browser TTS directly
        // TODO: Re-enable Sarvam TTS once endpoint is confirmed
        console.log('🔄 Using browser TTS (Sarvam TTS temporarily disabled)');
        this.fallbackBrowserTTS(translatedText, targetLanguage);
    }

    playAudio(audioUrl) {
        console.log('🎵 Playing audio from URL:', audioUrl);
        const audio = new Audio(audioUrl);

        audio.oncanplaythrough = () => {
            console.log('▶️ Audio ready, starting playback');
            audio.play();
        };

        audio.onended = () => {
            console.log('⏹️ Audio playback finished');
            this.updateStatus('🎤 Listening...');
        };

        audio.onerror = (error) => {
            console.error('❌ Audio playback error:', error);
            this.showMessage('⚠️ Audio playback failed', 'warning');
            this.updateStatus('🎤 Listening...');
        };

        // Fallback in case oncanplaythrough doesn't fire
        audio.play().catch(error => {
            console.error('❌ Audio play error:', error);
            this.showMessage('⚠️ Audio playback failed', 'warning');
            this.updateStatus('🎤 Listening...');
        });
    }

    fallbackBrowserTTS(text, language) {
        console.log('🎤 Using browser TTS fallback for:', text, 'in language:', language);

        // Map language codes to browser-supported speech synthesis languages
        const speechLangMap = {
            'en-IN': 'en-IN',  // English (India) - supported
            'hi-IN': 'hi-IN',  // Hindi - supported
            'mr-IN': 'hi-IN',  // Marathi -> fallback to Hindi
            'kn-IN': 'hi-IN'   // Kannada -> fallback to Hindi
        };

        const speechLang = speechLangMap[language] || 'en-IN';
        console.log('🎤 Using speech language:', speechLang, '(original:', language, ')');

        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = speechLang;
            utterance.rate = 0.85;
            utterance.pitch = 1;
            utterance.volume = 0.9;

            utterance.onstart = () => {
                console.log('▶️ Browser TTS started');
                this.updateStatus('🔊 Speaking translation (fallback)...');
            };

            utterance.onend = () => {
                console.log('⏹️ Browser TTS ended');
                this.updateStatus('🎤 Listening...');
            };

            utterance.onerror = (event) => {
                console.error('❌ Browser TTS error:', event.error);
                this.showMessage('⚠️ Speech synthesis failed', 'warning');
                this.updateStatus('🎤 Listening...');
            };

            try {
                window.speechSynthesis.speak(utterance);
                console.log('📢 Browser TTS speak() called');
            } catch (error) {
                console.error('💥 Browser TTS exception:', error);
                this.showMessage('⚠️ Speech synthesis error', 'warning');
                this.updateStatus('🎤 Listening...');
            }
        } else {
            console.error('❌ Browser TTS not supported');
            this.showMessage('⚠️ Speech synthesis not available', 'warning');
            this.updateStatus('🎤 Listening...');
        }
    }

    addMessageToChat(text, speaker, type) {
        const containerId = speaker === 'doctor' ? 'doctor-messages' : 'patient-messages';
        const container = document.getElementById(containerId);

        console.log(`🔍 Looking for container: ${containerId}, found:`, container);

        if (container) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${type}`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';

            if (type === 'translation') {
                contentDiv.innerHTML = `<small style="opacity: 0.7;">Translation:</small><br>${text}`;
            } else {
                const emoji = speaker === 'doctor' ? '👨‍⚕️' : '👤';
                contentDiv.innerHTML = `<small style="opacity: 0.7;">${emoji} Original:</small><br>${text}`;
            }

            messageDiv.appendChild(contentDiv);
            container.appendChild(messageDiv);

            console.log(`✅ Added message to ${containerId}:`, text);

            // Auto-scroll to bottom
            container.scrollTop = container.scrollHeight;
        }
    }

    updateStatus(message) {
        const statusDiv = document.getElementById('status-display');
        if (statusDiv) {
            statusDiv.textContent = message;
        }
    }

    updateButtonState(isListening) {
        const button = document.getElementById('start-stop-btn');
        if (button) {
            if (isListening) {
                button.textContent = '⏹️ Stop Listening';
                button.classList.remove('ready');
                button.classList.add('listening');
            } else {
                button.textContent = '🎤 Start Listening';
                button.classList.remove('listening');
                button.classList.add('ready');
            }
        }
    }

    showMessage(text, type = 'info') {
        const messagesDiv = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;

        messagesDiv.appendChild(messageDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);

        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Voice Translator...');
    try {
        window.voiceTranslator = new VoiceTranslator();
        console.log('Voice Translator initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Voice Translator:', error);
        const messagesDiv = document.getElementById('messages');
        if (messagesDiv) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message error';
            errorDiv.textContent = 'JavaScript initialization failed: ' + error.message;
            messagesDiv.appendChild(errorDiv);
        }
    }
});