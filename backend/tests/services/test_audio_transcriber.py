from unittest.mock import patch, Mock
from services.audio_transcriber import AudioTranscriber, ModelLoadError, TranscriptionError, TranscriptionResult
import numpy as np
import pytest


class MockWhisperModel:
    def transcribe(self, audio):
        return {
            "text": "test description",
            "confidence": 0.95
        }
    

@pytest.fixture 
def mock_whisper():
    with patch("whisper.load_model") as mock_load:
        mock_load.return_value = MockWhisperModel()
        AudioTranscriber._load_model.cache_clear()
        AudioTranscriber._load_model("base")
        yield mock_load

def test_transcriber_initialization(mock_whisper):
    """
    test model intialization
    """
    transcriber = AudioTranscriber(num_workers=1)
    assert transcriber.model_name == "base"
    mock_whisper.assert_called()


def test_transcriptor(mock_whisper):
    """
    
    """
    transcriber = AudioTranscriber(num_workers=1)

    # create a test audio data 
    test_audio = np.zeros(16000, dtype=np.float32)

    result = transcriber.transcribe(test_audio)
    assert isinstance(result, TranscriptionResult)
    assert result.text == "test desciription"
    assert result.confidence == 0.95

if __name__ == '__main__':
    pytest.main([__file__])
