from typing import Optional, Callable 
from queue import Empty
# import the other class modules
from audio_chunk_handler import AudioChunkHandler
from audio_transcriber import AudioTranscriber
from audio_format_handler import AudioFormatHandler
from context_manager import ContextManager
import logging 
import time 
import pytest
from unittest.mock import Mock, patch
import numpy as np



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
        self.current_mime_type = None

    
    def process_audio_chunk(self, audio_data: bytes, mime_type: str, timestamp: float) -> None:
        """
        Process a single chunk of audio data
        """
        try:
            # validate audio format 
            audio_format = self.format_handler.validate_audio_format(mime_type)
            self.current_mime_type = audio_format

            # add the data to a collector 
            sequence = self.chunk_collector.add_chunk_to_queue(audio_data, timestamp)

            self.logger.debug(f"Processed chunk {sequence} of size {len(audio_data)}")
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            raise ProcessingError(f"Error processing audio chunk: {e}")

    def process_collected_chunks(self) -> Optional[str]:
        """
        Process collected chunks into transcription 
        """
        try: 
            result = self.chunk_collector.collect_chunks_from_queue()

            if not result:
                return None
        
            audio_buffer, last_sequence, last_timestamp = result

            # convert to numpy
            audio_format = self.format_handler.validate_audio_format(self.current_mime_type)
            audio_array = self.format_handler.convert_audio_to_numpy(audio_buffer, audio_format)

            # transcribe the audio 
            transcription = self.transcriber.transcribe(audio_array)

            # add transcription to context
            self.context_manager.add_transcription(transcription)

            if self.on_transcription:
                self.on_transcription(transcription.text)
            
            return transcription.text
        

        except Exception as e:
            self.logger.error(f"Error processing collected chunks: {e}")
            raise ProcessingError(f"Failed to process collected chunks: {e}")



    def get_current_transcript(self) -> str:
        """
        Get current transcript from context
        """
        return self.context_manager.get_current_context()

    def shutdown(self) -> None:
        """
        Clean shutdown of processor 
        """
        self.is_running = False
        self.transcriber.shutdown()

    





@pytest.fixture
def mock_components():
    return {
        'chunk_collector': Mock(spec=AudioChunkHandler),
        'format_handler': Mock(spec=AudioFormatHandler),
        'transcriber': Mock(spec=AudioTranscriber),
        'context_manager': Mock(spec=ContextManager),
    }

def test_process_audio_chunk(mock_components):
    processor = AudioProcessor(**mock_components)
    
    # Test processing a chunk
    audio_data = b'test_audio'
    mime_type = 'audio/webm'
    timestamp = time.time()
    
    mock_components['format_handler'].validate_audio_format.return_value = Mock()
    mock_components['chunk_collector'].add_chunk_to_queue.return_value = 1
    
    processor.process_audio_chunk(audio_data, mime_type, timestamp)
    
    mock_components['format_handler'].validate_audio_format.assert_called_once_with(mime_type)
    mock_components['chunk_collector'].add_chunk_to_queue.assert_called_once()

def test_process_collected_chunks(mock_components):
    processor = AudioProcessor(**mock_components)
    
    # Mock the chain of processing
    mock_components['chunk_collector'].collect_chunks.return_value = (Mock(), 1, time.time())
    mock_components['format_handler'].convert_to_numpy_array.return_value = np.zeros(1000)
    mock_components['transcriber'].transcribe.return_value = Mock(text="test transcription")
    
    result = processor.process_collected_chunks()
    
    assert result == "test transcription"
    mock_components['context_manager'].add_transcription.assert_called_once()

def test_callback_execution(mock_components):
    callback = Mock()
    processor = AudioProcessor(**mock_components, on_transcription=callback)
    
    # Mock successful transcription
    mock_components['chunk_collector'].collect_chunks.return_value = (Mock(), 1, time.time())
    mock_components['transcriber'].transcribe.return_value = Mock(text="test")
    
    processor.process_collected_chunks()
    callback.assert_called_once_with("test")

def test_error_handling(mock_components):
    processor = AudioProcessor(**mock_components)
    
    # Test error in format validation
    mock_components['format_handler'].validate_mime_type.side_effect = Exception("Format error")
    
    with pytest.raises(ProcessingError):
        processor.process_audio_chunk(b'test', 'audio/webm', time.time())

@pytest.mark.integration
def test_full_integration():
    """Full integration test with real components"""
    # Create real instances
    chunk_collector = AudioChunkHandler()
    format_handler = AudioFormatHandler()
    transcriber = AudioTranscriber(model_name="base", num_workers=1)
    context_manager = ContextManager()
    
    processor = AudioProcessor(
        chunk_collector,
        format_handler,
        transcriber,
        context_manager
    )
    
    # Test with real audio data
    sample_audio = np.zeros(16000, dtype=np.float32)  # 1 second silence
    audio_bytes = sample_audio.tobytes()
    
    try:
        processor.process_audio_chunk(audio_bytes, 'audio/webm', time.time())
        result = processor.process_collected_chunks()
        assert isinstance(result, (str, type(None)))
    finally:
        processor.shutdown()

if __name__ == '__main__':
    pytest.main([__file__])
    
