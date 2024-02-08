import re
import uuid
from fastapi import FastAPI, WebSocket, Query, HTTPException, Depends, Request
from starlette.middleware.cors import CORSMiddleware
from typing import Optional
from starlette.websockets import WebSocketState
import random
import uvicorn
import jwt
from asgiref.sync import sync_to_async
from rest_framework import exceptions
import os
from django import setup
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_app_backend.settings")
django.setup()

from hotel.models import Owner
from customer.models import Customer


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                image_url = user_info.hotel_name
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

class JWTAuthentication:
    async def authenticate(self, request, token, user_type):
        if token:
            try:
                payload = jwt.decode(token, 'secret', algorithms=['HS256'])
            except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
                print(e)
                raise exceptions.AuthenticationFailed('Token is invalid')
        else:
            raise exceptions.AuthenticationFailed('Token is required')

        user = None

        try:
            user_id = payload.get('user_id')
            if user_type == 'owner':
                user = await self.get_business_owner(user_id)
                print(user,"this is test")
            elif user_type == 'customer':
                user = await self.get_customer(user_id)
            else:
                raise exceptions.AuthenticationFailed('Invalid user_type in token.')

        except Exception as e:
            print(e)
            raise exceptions.AuthenticationFailed('Error fetching user from the database')

        if not user:
            raise exceptions.AuthenticationFailed('User not found.')

        request.user = user

        return (request.user, token)
    
    @sync_to_async
    def get_business_owner(self, user_id):
        try:
            return Owner.objects.get(id=user_id)
        except Owner.DoesNotExist:
            return None

    @sync_to_async
    def get_customer(self, user_id):
        try:
            return Customer.objects.get(id=user_id)
        except Customer.DoesNotExist:
            return None
    
async def verify_token(token: str, user_type: str, request: Request = Depends()):
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
        print(e)
        raise HTTPException(status_code=400, detail="Authorization Token is invalid")

    jwt_auth = JWTAuthentication()
    user, token = await jwt_auth.authenticate(request, token, user_type)

    if not user:
        raise HTTPException(status_code=400, detail="Authorization Token is invalid")

    return user

async def get_current_user(token: str, user_type: str):
    """Helper function for auth with Firebase."""
    if not token:
        return ""
    try:
        user_info = await verify_token(token, user_type)
        return user_info
    except HTTPException as e:
        raise e

owner_id = None
active_rooms = {}


@app.websocket("/ws/room_connection")
async def room_connection(
    websocket: WebSocket,
    user_type: str = Query(None),
    room_id: str = Query(None),
    token: str = Query(None)
):
    global owner_id
    
    user_info = await get_current_user(token, user_type)
    if not user_info:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    try:
        if isinstance(user_info, Customer):
            owner_id = id(websocket)
            await manager.connect(websocket)

        if room_id:
            if room_id in active_rooms and active_rooms[room_id] == owner_id:
                if isinstance(user_info, Owner):
                    await manager.connect(websocket)
                    try:
                        await manager.update_active_room(websocket, room_id)
                        await websocket.send_text(f"You are now connected to room {room_id}.")
                    except Exception as e:
                        print("this is error")
                    message = f"Owner {user_info.hotel_name} entered the room."
                    await manager.send_personal_message(message, owner_id, user_info, room_id)
                else:
                    await websocket.close(code=1008, reason="Owner ID not found.")
            else:
                await websocket.close(code=1008, reason="Invalid Room ID or Room not found.")
        else:
            room_id = generate_unique_room_id()
            await manager.save_active_room(websocket, room_id)
            active_rooms[room_id] = owner_id
            await websocket.send_text(f"Room ID: {room_id}")
            await websocket.send_text("You are now connected to the room.")
                 
    except Exception as e:
        print("An error occurred:", e)


if __name__ == '__main__':
    uvicorn.run("websocket:app", host="0.0.0.0", port=7000, log_level="info", reload=True)
