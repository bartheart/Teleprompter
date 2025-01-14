from queue import Queue, Empty
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
        audio buffer - queue, max length: 30 => 3 seconds audio 
        result queue - queue, max length not capped
        context - deque to serve as rolling window 
        pool size of 5 -> 5 cores to process the transctiption
        """
        self.buffer_queue = Queue(maxsize= 30) 
        self.result_queue = Queue()
        self.context = deque(maxlen=45)
        self.context_lock = Lock()
        self.process_pool = Pool(processes=5)
        self.sequence_counter = 0
        self.sample_rate = 16000
        self.min_chunk_to_process = 100
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

    def _get_buffer_queue_size (self) -> int:
        """
        get the size of the buffer queue
        """
        return self.buffer_queue.qsize()
            

    def _process_chunks(self):
        """
        process the audio chunks in the buffer queue
        """
        while True:
            
            try:
                audio_buffer, last_sequence_number = self._collect_chunks_from_queue()

                # compile parameters to pass to the process pool 
                audio_params = {
                    'chunk': audio_buffer.getvalue(),
                    'mime_type': self.mime_type,
                    'sample_rate': self.sample_rate,
                }

                audio_transcription = self.process_pool.apply_async(self._transcribe_chunk, (audio_params, ))
            
            
                self._handle_result(audio_transcription.get(), last_sequence_number)
            
            except Exception as e:
                continue

    
    def _collect_chunks_from_queue(self) -> tuple[BytesIO, int]:
        """
        collect the chunks from the buffer queue
        """
        audio_buffer = BytesIO()
        chunks_processed = 0
        last_sequence = None
        retry_count = 0
        max_retries = 3


        try:
            while chunks_processed < self.min_chunk_to_process:
                try: 
                    sequence, chunk = self.buffer_queue.get(timeout=0.1)
                    audio_buffer.write(chunk)
                    last_sequence = sequence
                    chunks_processed += 1

                    if chunks_processed >= 10:
                        break
                except Empty:
                    if chunks_processed < 10:
                        if retry_count < max_retries:
                            retry_count += 1
                            continue
                        if chunks_processed > 0:
                            break
                    else:
                        break
                    
            
            audio_buffer.seek(0)
            return audio_buffer, last_sequence
        except Exception as e:
            if chunks_processed > 0:
                audio_buffer.seek(0)
                return audio_buffer, last_sequence
            raise
    

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


    @staticmethod
    def _transcribe_chunk(params) -> str:
        """
        transcribe the audio chunk
        """
        if not params['chunk']:
            print("Empty chunk received")
            raise Exception("No audio chunk found")
        
        audio_buffer = BytesIO(params['chunk'])

        try: 
            print(f"Processing chunk size: {len(params['chunk'])} bytes")
            print(f"Mime type: {params['mime_type']}")

            audio_segment = AudioSegment.from_file(
                audio_buffer,
                codec='opus',
                format=params['mime_type'],
                parameters=[
                    "-loglevel", "debug", 
                    "-ar", str(params.get('sample_rate', '16000')),
                    "-ac", "1",  # Force mono channel
                    "-vn",
                    "-fflags", "+igndts",  # Add tolerance for timestamp errors
                    "-flags", "low_delay"
                ]
            )   
            print(f"Audio segment created successfully: {len(audio_segment)} ms")

            samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)/32768.0
            print(f"Samples shape: {samples.shape}")

            # Load model in worker process
            model = whisper.load_model("turbo")
            return model.transcribe(samples).get("text", "No text found")
        except Exception as e:
            print(f"Audio processing error: {e}")
            return "No text found"