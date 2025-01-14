import pytest
from io import BytesIO
import time 
from unittest.mock import patch, Mock
from services.test_audio_chunk_handler import AudioChunkHandler, AudioChunk, BufferQueueFull, ChunkProcessingError


def test_add_chunk_to_queue():
    """
    test the add_chunk_to_queue method
    """
    collector = AudioChunkHandler()
    timestamp = time.time()

    # add a chunk to the queue
    sequence = collector.add_chunk_to_queue(b"test_audio", timestamp)
    assert sequence == 0
    assert collector.buffer_queue.qsize() == 1

    # test buffer is full 
    for _ in range(39):
        collector.add_chunk_to_queue(b"test_audio", timestamp)
    with pytest.raises(BufferQueueFull):
        collector.add_chunk_to_queue(b"test_audio_3", timestamp)


def test_collect_chunks_from_queue():
    """
    test the collect_chunks_from_queue method
    """
    collector = AudioChunkHandler()
    timestamp = time.time()

    # add test chunks 
    collector.add_chunk_to_queue(b"test_audio_1", timestamp)
    collector.add_chunk_to_queue(b"test_audio_2", timestamp)

    # test the collection
    buffer, sequence, timestamp = collector.collect_chunks_from_queue()
    assert isinstance(buffer, BytesIO)
    assert sequence == 1

    buffer.seek(0)
    content = buffer.read()
    assert content == b"test_audio_1test_audio_2"

if __name__ == '__main__':
    pytest.main([__file__])