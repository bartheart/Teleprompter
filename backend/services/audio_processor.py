from typing import Optional, Callable 
from queue import Empty
# import the other class modules
from audio_chunk_handler import AudioChunkHandler
from audio_transcriber import AudioTranscriber
from audio_format_handler import AudioFormatHandler
from context_manager import ContextManager
import logging 
import time 




class ProcessingError(Exception):
    pass


class AudioProcessor:
    def __init__(self, chunk_collector: AudioChunkHandler, format_handler: AudioFormatHandler, transcriber: AudioTranscriber, context_manager: ContextManager, on_transcription: Optional[Callable[[str], None]] = None):
        self.chunk_collector = chunk_collector
        self.format_handler = format_handler
        self.transcriber = transcriber
        self.context_manager = context_manager
        self.on_transcription  = on_transcription
        self.logger = logging.getLogger(__name__)
        self.is_running = True

    
    def process_audio_chunk(self, audio_data: bytes, mime_type: str, timestamp: float) -> None:
        """
        Process a single chunk of audio data
        """
        try:
            # validate audio format 
            audio_format = self.format_handler.validate_audio_format(mime_type)

            # add the data to a collector 
            self.chunk_collector.add_chunk_to_queue(audio_data)
        except Exception as e:
            raise

    def process_collected_chunks(self) -> Optional[str]:
        """
        Process collected chunks into transcription 
        """
        pass

    def get_current_transcript(self) -> str:
        """
        Get current transcript from context
        """

    def shutdown(self) -> None:
        """
        Clean shutdown of processor 
        """

    

    
