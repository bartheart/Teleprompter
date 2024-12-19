from fastapi import APIRouter
import socketio
from typing import Any


# initialize the app router 
router = APIRouter()

# create the socket instance with ASIG support 
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