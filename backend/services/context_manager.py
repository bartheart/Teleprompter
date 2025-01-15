from typing import List, Optional 
from dataclasses import dataclass
from collections import deque
from time import time
from threading import Lock
import logging 
import pytest


class ContextError:
    pass

@dataclass
class TranscribedSegment:
    text: str
    timestamp: float
    sequence_number: int


class ContextManager:
    def __init__(self, max_context_size: int = 45):
        self.context = deque(maxlen=max_context_size)
        self.context_lock = Lock()
        self.logger = logging.getLogger(__name__)
        self.last_sequence = -1

    
    def add_transcription(self, transcribed_segment: TranscribedSegment) -> bool:
        """
        add new context token to the queue 
        """
        try:
            with self.context_lock:
                # check the sequence ordering 
                if self.last_sequence > transcribed_segment.sequence_number:
                    self.logger.warning(f"Out of order sequence recived: {transcribed_segment.sequence_number}")
                    return False 
                
                self.context.append(transcribed_segment)
                self.last_sequence = transcribed_segment.sequence_number
                return True 
        except Exception as e:
            self.logger.error(f"Error adding transcription: {str(e)}")
            raise ContextError(f"Error adding transcription: {str(e)}")
        
    def get_current_context(self, window_seconds: float = 30.0) -> str:
        """
        get concatenated text from the recent context in the window 
        """
        try:
            with self.context_lock:
                current_time = time()
                recent_segmnets = [
                    segment.text for segment in self.context if current_time - segment.timestamp <= window_seconds
                ]
                return " ".join(recent_segmnets)
        except Exception as e:
            self.logger.error(f"Error reteriving current context: {str(e)}")
            raise ContextError(f"Error reteriving current context: {str(e)}")


    def clear_context(self) -> None:
        """
        clean the context 
        """
        with self.context_lock:
            self.context.clear()
            self.last_sequence = -1


def test_transcription_addition():
    """
    test the adding the transcribed text to context
    """
    context_manager = ContextManager(max_context_size=3)
    current_time = time()

    # test adding transcription 
    test_segment_1 = TranscribedSegment(
        "hello",
        current_time,
        0
    )
    test_segment_2 = TranscribedSegment(
        "world",
        current_time,
        1
    )
    context_added_1 = context_manager.add_transcription(test_segment_1)
    context_added_2 = context_manager.add_transcription(test_segment_2)

    assert context_added_1 == True
    assert context_added_2 == True


    # test context retrival 
    context = context_manager.get_current_context()
    assert "hello world" in context
    
    # test the max size
    test_segment_1 = TranscribedSegment(
        "test",
        current_time,
        0
    )
    test_segment_2 = TranscribedSegment(
        "overflow",
        current_time,
        1
    )
    context_added_1 = context_manager.add_transcription(test_segment_1)
    context_added_2 = context_manager.add_transcription(test_segment_2)
    context = context_manager.get_current_context()
    assert "hello word" not in context


if __name__ == '__main__':
    pytest.main([__file__])
