from dataclasses import dataclass
from multiprocessing import Pool
from functools import lru_cache
import numpy as np
import whisper 
import logging
import pytest
from unittest.mock import patch, Mock


class ModelLoadError():
    pass

class TranscriptionError():
    pass

@dataclass
class TranscriptionResult:
    text: str
    confidence: float


class AudioTranscriber:
    def __init__(self, model_name: str = 'base', num_workers: int = 4):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        try:
            self.process_pool = Pool(
                processes=num_workers,
                initializer=self._init_worker,
                initargs=(model_name,)
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize worker pool: {e}")
            raise ModelLoadError(f"Failed to initialize worker pool: {e}")
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model(model_name: str) :
        """
        Load whisper model - cached for each process 
        """
        try:
            return whisper.load_model(model_name)
        except Exception as e:
            raise ModelLoadError(f"Failed to load the model: {model_name}; {e}")
        

    @staticmethod
    def _init_worker(model_name: str):
        """
        initialize the worker by loading the model
        """
        try: 
            AudioTranscriber._load_model(model_name)
        except Exception as e:
            logging.error(f"Failed to initalize worker: {e}")

    
    def transcribe(self, audio_array: np.ndarray) -> TranscriptionResult:
        """
        transcribe audio using worker pool
        """
        try:
            result = self.process_pool.apply_async(self._transcribe_worker, (audio_array,))
            return result.get(timeout=5)
        except Exception as e:
            self.logger.error(f"Trancription failed: {e}")
            raise TranscriptionError(f"Trancription failed: {e}")

    @staticmethod
    def _transcribe_worker(audio_array: np.ndarray) -> TranscriptionResult:
        """
        wokrer function for transcription
        """
        try:
            # use the cahced model
            model = AudioTranscriber._load_model("base")
            result = model.transcribe(audio_array)
            return TranscriptionResult(
                text = result.get("text", "").strip(),
                confidence = result.get("confidence", 0.00)
            )
        except Exception as e:
            logging.error(f"Worker transcription has failed: {e}")
            raise TranscriptionError (f"Worker transcription has failed: {e}")
    

    def shutdown(self):
        """
        clean shutdown of the worker pool
        """

        if hasattr(self, 'process_pool'):
            self.process_pool.close()
            self.process_pool.join()

        
        

        

class MockWhisperModel:
    def transcribe(self, audio):
        return {
            "text": "test transcription",
            "confidence": 0.95
        }

@pytest.fixture 
def mock_whisper():
    with patch("whisper.load_model", autospec=True) as mock_load:
        mock_load.return_value = MockWhisperModel()
        AudioTranscriber._load_model.cache_clear()
        AudioTranscriber._load_model("base")
        yield mock_load

@pytest.fixture 
def transcriber(mock_whisper):
    transcription = AudioTranscriber(model_name='base', num_workers=1)
    yield transcription 
    transcription.shutdown()

@pytest.fixture 
def sample_audio():
    return np.zeros(16000, dtype=np.float32)

def test_transcriber_initialization(mock_whisper):
    """
    
    """
    transcriber = AudioTranscriber(num_workers=4)
    assert transcriber.model_name == "base"
    mock_whisper.assert_called_once_with('base')
    transcriber.shutdown()

def test_transcribe_success(transcriber, sample_audio):
    result = transcriber.transcribe(sample_audio)
    assert isinstance(result, TranscriptionResult)
    assert result.text == "test transcription"
    assert result.confidence == 0.95


# def test_transcriptor(mock_whisper):
#     """
    
#     """
#     transcriber = AudioTranscriber(num_workers=1)

#     # create a test audio data 
#     test_audio = np.zeros(16000, dtype=np.float32)

#     result = transcriber.transcribe(test_audio)
#     assert isinstance(result, TranscriptionResult)
#     assert result.text == "test description"
#     assert result.confidence == 0.95

if __name__ == '__main__':
    pytest.main([__file__])
