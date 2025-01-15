from unittest.mock import Mock, patch
from services.context_manager import TranscribedSegment, ContextError, ContextManager
from time import time
import pytest


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


def test_context_ordering():
    context = ContextManager()


if __name__ == '__main__':
    pytest.main([__file__])
