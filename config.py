import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sarvam AI Configuration
SARVAM_API_KEY = os.getenv('SARVAM_API_KEY', 'sk_dycpbtsd_9sAcw9RbABTESWPzJ6IsQBYC')

# Language Configuration for Doctor-Patient Translation
LANGUAGE_CONFIG = {
    'english': 'en-IN',
    'hindi': 'hi-IN',
    'marathi': 'mr-IN',
    'kannada': 'kn-IN'
}

# API Base URL (based on documentation)
SARVAM_BASE_URL = "https://api.sarvam.ai"

# Supported language pairs for translation
SUPPORTED_TRANSLATIONS = {
    ('en-IN', 'hi-IN'),
    ('en-IN', 'mr-IN'),
    ('en-IN', 'kn-IN'),
    ('hi-IN', 'en-IN'),
    ('hi-IN', 'mr-IN'),
    ('hi-IN', 'kn-IN'),
    ('mr-IN', 'en-IN'),
    ('mr-IN', 'hi-IN'),
    ('mr-IN', 'kn-IN'),
    ('kn-IN', 'en-IN'),
    ('kn-IN', 'hi-IN'),
    ('kn-IN', 'mr-IN')
}
