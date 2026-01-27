#!/usr/bin/env python3
"""
Tests for Sarvam AI Translation Service
Run with: python -m pytest test_sarvam.py -v
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sarvam_service import SarvamService, DoctorPatientTranslator, SarvamTranslationError
from config import LANGUAGE_CONFIG

class TestSarvamService:
    """Test cases for SarvamService"""

    def test_language_code_conversion(self):
        """Test language name to code conversion"""
        service = SarvamService()

        assert service.get_language_code("english") == "en-IN"
        assert service.get_language_code("hindi") == "hi-IN"
        assert service.get_language_code("marathi") == "mr-IN"
        assert service.get_language_code("kannada") == "kn-IN"
        assert service.get_language_code("en-IN") == "en-IN"  # Already a code

    def test_validate_languages_valid(self):
        """Test validation of valid languages"""
        service = SarvamService()

        source, target = service.validate_languages("english", "hindi")
        assert source == "en-IN"
        assert target == "hi-IN"

    def test_validate_languages_invalid(self):
        """Test validation of invalid languages"""
        service = SarvamService()

        with pytest.raises(SarvamTranslationError):
            service.validate_languages("invalid", "english")

        with pytest.raises(SarvamTranslationError):
            service.validate_languages("english", "invalid")

    @patch('requests.Session.post')
    def test_translate_text_success(self, mock_post):
        """Test successful translation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "translated_text": "नमस्ते दुनिया"
        }
        mock_post.return_value = mock_response

        service = SarvamService()
        result = service.translate_text("Hello world", "en-IN", "hi-IN")

        assert result == "नमस्ते दुनिया"
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_translate_text_api_error(self, mock_post):
        """Test API error handling"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_post.return_value = mock_response

        service = SarvamService()

        with pytest.raises(SarvamTranslationError):
            service.translate_text("Hello", "en-IN", "hi-IN")

    @patch('requests.Session.post')
    def test_translate_text_network_error(self, mock_post):
        """Test network error handling"""
        from requests.exceptions import ConnectionError
        mock_post.side_effect = ConnectionError("Network unreachable")

        service = SarvamService()

        with pytest.raises(SarvamTranslationError):
            service.translate_text("Hello", "en-IN", "hi-IN")

class TestDoctorPatientTranslator:
    """Test cases for DoctorPatientTranslator"""

    def test_supported_patient_languages(self):
        """Test getting supported patient languages"""
        service = SarvamService()
        translator = DoctorPatientTranslator(service)

        languages = translator.get_supported_patient_languages()
        assert "english" not in languages
        assert "hindi" in languages
        assert "marathi" in languages
        assert "kannada" in languages

    @patch.object(SarvamService, 'translate_text')
    def test_doctor_to_patient_translation(self, mock_translate):
        """Test doctor to patient translation"""
        mock_translate.return_value = "नमस्ते"

        service = SarvamService()
        translator = DoctorPatientTranslator(service)

        result = translator.doctor_to_patient("Hello", "hindi")

        assert result == "नमस्ते"
        mock_translate.assert_called_with("Hello", "en-IN", "hi-IN")

    @patch.object(SarvamService, 'translate_text')
    def test_patient_to_doctor_translation(self, mock_translate):
        """Test patient to doctor translation"""
        mock_translate.return_value = "Hello"

        service = SarvamService()
        translator = DoctorPatientTranslator(service)

        result = translator.patient_to_doctor("नमस्ते", "hindi")

        assert result == "Hello"
        mock_translate.assert_called_with("नमस्ते", "hi-IN", "en-IN")

def test_language_config():
    """Test language configuration"""
    assert len(LANGUAGE_CONFIG) == 4
    assert LANGUAGE_CONFIG["english"] == "en-IN"
    assert LANGUAGE_CONFIG["hindi"] == "hi-IN"
    assert LANGUAGE_CONFIG["marathi"] == "mr-IN"
    assert LANGUAGE_CONFIG["kannada"] == "kn-IN"

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
