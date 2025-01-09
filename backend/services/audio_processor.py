from queue import Queue
from collections import deque
from multiprocessing import Pool, Queue as MPqueue
from threading import Thread, Lock
from io import BytesIO
from pydub import AudioSegment
import numpy as np 
import whisper

class AudioProcessor:
    def __init__ (self):
        """
        buffer and result queues to store the audio
        context - deque to serve as rolling window 
        pool size of 5 -> 5 cores to process the transctiption
        """
        self.buffer_queue = Queue(maxsize= 30)
        self.result_queue = Queue()
        self.context = deque(maxlen=45)
        self.context_lock = Lock()
        self.process_pool = Pool(processes=5)
        self.sequence_counter = 0
        self.sample_rate = "16000"
        self.mime_type = ''

        # start the worker thread
        self.worker = Thread(target=self._process_chunks, daemon=True)
        self.worker.start()

        # load the trancription model 
        self.model = whisper.load_model("turbo")
        if not self.model:
            raise Exception("Failed to load the transcritption model")

    def update_mime_type(self, mime_string: str) -> None:
        """
        update the mime type of the audio the browser supports
        """
        # define a mime to type dictionary
        mime_to_extension = {
            'audio/webm': 'webm',
            'audio/webm;codecs=opus': 'webm',
            'audio/mp4': 'mp4',
            'audio/mp4;codecs=opus': 'mp4',
            'audio/ogg': 'ogg',
            'audio/ogg;codecs=opus': 'ogg',
        }

        # get the extension from the mime type 
        self.mime_type = mime_to_extension.get(mime_string, 'bin')
        

        
    def add_chunk_to_buffer(self, audio_data: bytes) -> None:
        """
        add the audio chunk to the buffer queue
        """
        try: 
            self.buffer_queue.put_nowait((self.sequence_counter, audio_data))
            self.sequence_counter += 1  
        except Queue.full:
            pass
            

    def _process_chunks(self):
        """
        process the audio chunks in the buffer queue
        """
        while True:
            sequence_number, audio_chunk = self.buffer_queue.get()
            audio_transcription = self.process_pool.apply_async(self._transcribe_chunk(audio_chunk))
            self._handle_result(audio_transcription.get(), sequence_number)


    def _handle_result(self, text: str, sequence_number: int):
        """
        handle the result of the transcription
        """
        with self.context_lock:
            tokens = text.split()
            self.context.extend(tokens)
            if len(self.context) >= 45:
                self.context.popleft()


    def get_context(self) -> str:
        """
        get the context of the audio
        """
        with self.context_lock:
            return " ".join(self.context)   



    def _transcribe_chunk(self, audio_chunk: bytes) -> str:
        """
        transcribe the audio chunk
        """
        audio_buffer = BytesIO(audio_chunk)
        audio_segment = AudioSegment.from_file(
            audio_buffer,
            codec= 'opus',
            format = self.mime_type,
            parameters=["-ar", self.sample_rate]
        )   

        samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)/32768.0
        return self.model.transcribe(samples).get("text", "No text found")
