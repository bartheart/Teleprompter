from unittest.mock import patch, Mock
from io import BytesIO
import numpy as np
import pytest 
from services.audio_format_handler import AudioFormat, AudioFormatHandler, AudioFormatError, ConversionError


def create_test_audio() -> BytesIO:
    """
    create a test audio 
    """
    sample_rate = 16000
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)

    # Convert to int16 and then to bytes
    audio_int16 = (audio * 32767).astype(np.int16)
    buffer = BytesIO(audio_int16.tobytes())
    return buffer

def test_mime_type_validation ():
    """
    test mime type validation 
    """

    format_handler = AudioFormatHandler()

    # test the mime types 
    format = format_handler.validate_audio_format('audio/webm;codecs=opus')

    assert format.mime_type == 'webm'
    assert format.codec == 'opus'

    format = format_handler.validate_audio_format('audio/mp4;codecs=opus')

    assert format.mime_type == 'mp4'
    assert format.codec == 'opus'


    # test with invalid mime type 
    with pytest.raises(AudioFormatError):
        format_handler.validate_audio_format('audio/invalid')



@pytest.mark.integration
def test_audio_to_numpy_conversion():
    """
    test audio to numpy conversion 
    """
    handler = AudioFormatHandler()
    audio_format = handler.validate_audio_format('audio/webm;codecs=opus')
    
    # Create test audio data
    audio_data = create_test_audio()
    
    with patch('pydub.AudioSegment.from_file') as mock_from_file:
        # Create mock audio segment
        mock_segment = Mock()
        mock_segment.get_array_of_samples.return_value = np.array([0, 16384, -16384], dtype=np.int16)
        mock_from_file.return_value = mock_segment
        
        # Perform conversion
        result = handler.convert_audio_to_numpy(audio_data, audio_format)
        
        # Verify conversion
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert np.max(np.abs(result)) <= 1.0
        
        # Verify mock was called correctly
        mock_from_file.assert_called_once()
        call_args = mock_from_file.call_args[1]
        assert call_args['format'] == 'webm'
        assert call_args['codec'] == 'opus'


def test_conversion_error():
    """
    test audio conversion faliure
    """
    format_handler = AudioFormatHandler()
    audio_format = format_handler.validate_audio_format('audio/webm;codecs=opus')
    test_audio = create_test_audio()

    with patch('pydub.AudioSegment.from_file') as mock_from_file:
        mock_from_file.side_effect = Exception("Conversion failed")


        with pytest.raises(ConversionError) as exc_info:
            format_handler.convert_audio_to_numpy(test_audio, audio_format)
        assert "Failed to convert audio to numpy"


@pytest.mark.integration 
def test_empty_audio_conversion_error():
    """
    test conversion with empty audio data 
    """
    format_handler = AudioFormatHandler()
    audio_format = format_handler.validate_audio_format('audio/webm;codecs=opus')
    empty_data = BytesIO(b"")

    with pytest.raises(ConversionError):
        format_handler.convert_audio_to_numpy(empty_data, audio_format)


if __name__ == '__main__':
    pytest.main([__file__])