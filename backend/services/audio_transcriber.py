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
