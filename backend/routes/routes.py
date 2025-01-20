from fastapi import APIRouter
import socketio
from typing import Any
from backend.services.audio_processor_2 import AudioProcessor

# initialize the app router 
router = APIRouter()

# create the socket instance with ASGI support 
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# create ASGI app 
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=router
)


# define the home route 
@router.get('/')
async def Home():
    return "Home route"


# socket io event handlers 
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('connect_response', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")




# define the audio processor class
audio_processor = AudioProcessor()


# to get the mime/ audio format from the browser
@sio.event 
async def mime_type(sid, mime_type: str):
    """
    get the mime type of the audio format
    """
    audio_processor.update_mime_type(mime_type)


# handle the event of sending audio packets 
@sio.event
async def audio_data(sid, audio_chunk: bytes):
    audio_processor.add_chunk_to_buffer(audio_chunk)
    context = audio_processor.get_context()
    print(context)