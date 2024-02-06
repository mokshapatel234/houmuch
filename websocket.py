import re
import uuid
from fastapi import FastAPI, WebSocket, Query, HTTPException
from starlette.middleware.cors import CORSMiddleware
from typing import Optional
from starlette.websockets import WebSocketState
import random
import uvicorn

class Singleton:
    _instances = {}

    @classmethod
    def get_instance(cls, args, *kwargs):
        """ Static access method. """
        if cls not in cls._instances:
            cls._instances[cls] = cls(*args, **kwargs)

        return cls._instances[cls]

    @classmethod
    def initialize(cls, args, *kwargs):
        """ Static access method. """
        if cls not in cls._instances:
            cls._instances[cls] = cls(*args, **kwargs)

class ConnectionManager(Singleton):
    def __init__(self):
        self.active_connections = []
        self.room_clients = {}

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()  
        except Exception as e:
            print(e)

    async def disconnect(self, websocket: WebSocket, room_id):
        self.room_clients[room_id].remove(websocket)
        print(f"Client #{id(websocket)} left the chat")

    async def save_active_room(self, websocket: WebSocket, room_id):
        self.room_clients[room_id] = [websocket]
        print(self.room_clients)
    
    async def update_active_room(self, websocket: WebSocket, room_id):
        self.room_clients[room_id].append(websocket)
        print(self.room_clients)

    async def remove_active_room(self, websocket: WebSocket, room_id):
        self.room_clients[room_id].pop(websocket)
        print(self.room_clients)

    async def send_message(self, message: str, websocket: WebSocket):
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_text(message)

    async def send_personal_message(self, message: str, receiver_id: int, user_info, room_id):
        for connection in self.room_clients[room_id]:
            if id(connection) == receiver_id:
                image_url = user_info.profile_image.url if user_info.profile_image else None
                combined_message = f"{message} Image URL: {image_url}"
                await connection.send_text(combined_message)

    async def broadcast_to_room(self, room_id: str, message: str):
        for websocket in self.room_clients[room_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Failed to send message to client : {e}")

manager = ConnectionManager() 

def generate_unique_room_id():
    return str(random.randint(1000000000, 9999999999))


active_rooms = {}


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/room_connection")
async def room_connection(
    websocket: WebSocket,
    user_type: str = Query(None),
    room_id: str = Query(None)
):
    if user_type == "customer":
        if room_id:
            await websocket.close(code=1008, reason="Room ID should not be provided by customers.")
            return
        else:
            room_id = generate_unique_room_id()
            await manager.save_active_room(websocket, room_id)
            active_rooms[room_id] = websocket
            await websocket.accept()  # Accept the WebSocket connection
            await websocket.send_text(f"Room ID: {room_id}")
            await websocket.send_text("You are now connected to the room.")

    elif user_type == "owner":
        if room_id and room_id in active_rooms:
            await manager.connect(websocket)
            await manager.update_active_room(websocket, room_id)
            await websocket.send_text(f"You are now connected to room {room_id}.")
        else:
            await websocket.close(code=1008, reason="Invalid Room ID or Room not found.")
    else:
        await websocket.close(code=1008, reason="Invalid User Type.")




if __name__ == '__main__':
    uvicorn.run("websocket:app", host="0.0.0.0", port=7000, log_level="info", reload=True)
