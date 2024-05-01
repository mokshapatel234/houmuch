import re
import uuid
from fastapi import FastAPI, WebSocket, Query, HTTPException, Depends, Request
from starlette.middleware.cors import CORSMiddleware
from typing import Optional
from starlette.websockets import WebSocketState
import random
import uvicorn
from fastapi import WebSocketDisconnect
import jwt
from asgiref.sync import sync_to_async
from rest_framework import exceptions
import os
from django import setup
import django
from typing import List
from django.db.models import Min
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_app_backend.settings")
django.setup()

from hotel.models import Owner, BiddingSession, Property, PropertyDeal, RoomInventory,BiddingAmount
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
        await websocket.close()

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
                combined_message = f"{message}"
                await connection.send_text(combined_message)

    async def send_combind_personal_message(self, message: str, receiver_ids: List[int], user_info, room_id):
        for connection in self.room_clients[room_id]:
            if id(connection) in receiver_ids:
                combined_message = f"{message}"
                await connection.send_text(combined_message)

    async def broadcast_to_room(self, room_id: str, message: str):
        for websocket in self.room_clients[room_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Failed to send message to client : {e}")

manager = ConnectionManager()

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


@sync_to_async
def save_bidding_session(customer_id):
    existing_open_session = BiddingSession.objects.filter(customer_id=customer_id, is_open=True).first()
    
    if existing_open_session:
        return "You have already created one session."  # or raise Exception("Customer already has an open session")
    
    # Create a new session for the customer
    result_instance = BiddingSession.objects.create(is_open=True, customer_id=customer_id)
    
    # Return the ID of the created session
    return result_instance.id

@sync_to_async
def save_property_deal(session_id, customer_id, room_id):
    try:
        room_inventory = RoomInventory.objects.get(id=room_id) 
        property_deal = PropertyDeal.objects.create(
            session_id=session_id,
            customer_id=customer_id,  
            roominventory=room_inventory,
            is_winning_bid=False
        )
        return property_deal.id
    except Exception as e:
        print("An error occurred while creating property deal:", e)
        return None

@sync_to_async
def featch_property_deal(session_id, room_id):
    try:
        property_deal_query = PropertyDeal.objects.filter(
            session_id=session_id,
            roominventory=room_id
        ).first()
        print(property_deal_query, "this is to get id")
        return property_deal_query
    except Exception as e:
        print("An error featch:", e)
        return None

@sync_to_async
def update_is_open(session_id):
    bidding_session = BiddingSession.objects.get(id=session_id)
    bidding_session.is_open = False
    bidding_session.save()

@sync_to_async
def update_property_deal_winning_bid_status(property_deal_id):
    property_deal = PropertyDeal.objects.get(id=property_deal_id)
    property_deal.is_winning_bid = True
    property_deal.save()

@sync_to_async
def get_all_quotes_for_session_sync(session_id):
    try:
        # Query all bidding amounts for the given session ID
        bidding_amounts = BiddingAmount.objects.filter(
            property_deal__session_id=session_id
        )

        # Extract relevant information from each bidding amount
        quotes = []
        for amount in bidding_amounts:
            room_id = amount.property_deal.roominventory_id
            property_id = RoomInventory.objects.get(id=room_id).property_id
            hotel_nick_name = Property.objects.filter(id=property_id).values_list('hotel_nick_name', flat=True).first()
            
            quote_info = {
                'room_id': room_id,
                'hotel_nick_name': hotel_nick_name,
                'amount': amount.amount,
            }
            quotes.append(quote_info)

        return quotes
    except Exception as e:
        print(f"Error retrieving quotes for session {session_id}: {e}")
        return []

@sync_to_async
def get_last_bidding_amount(property_deal_id):
    return BiddingAmount.objects.filter(property_deal_id=property_deal_id).aggregate(Min('amount'))

async def create_bidding_session(customer_id):
    print("Creating bidding session...")
    try:
        bidding_session_id = await save_bidding_session(customer_id)
        return bidding_session_id
    except Exception as e:
        print("An error occurred while creating bidding session:", e)
        return None


async def create_property_deal(session_id, customer_id, room_id):
    try:

        deal_id = await save_property_deal(session_id, customer_id, room_id)
        return deal_id
                                 
    except Exception as e:
        print("An error occurred while creating property deal:", e)
        return None


async def get_property_deal(session_id, room_id):
    try:
        await featch_property_deal(session_id, room_id)
                                 
    except Exception as e:
        print("An error:", e)
        return None


async def get_property_deal_id(session_id: str, room_id: int) -> Optional[int]:
    try:
        property_deal = await sync_to_async(PropertyDeal.objects.get)(session_id=session_id, roominventory_id=room_id)
        return property_deal.id
    except PropertyDeal.DoesNotExist:
        return None

async def get_property_deal_owner_id(property_deal_id: int) -> Optional[int]:
    try:
        property_deal = await sync_to_async(PropertyDeal.objects.get)(id=property_deal_id)
        owner_id = await sync_to_async(lambda: property_deal.roominventory.property.owner.id)()
        return owner_id
    except PropertyDeal.DoesNotExist:
        return None

# async def send_loser_messages(session_id: str, user_info: Customer, room_id: int, owner_id: int):
#     # Get all connections in the session
#     connections = session_connections.get(session_id, [])
    
#     for conn in connections:
#         # Skip sending message to the owner
#         if await get_current_user(conn,"owner") == owner_id:
#             continue
        
#         await manager.send_personal_message(
#             f"Sorry! Your bid for room {room_id} has not been accepted. You lost the bid.",
#             id(conn),
#             user_info,
#             session_id
#         )

async def get_hotel_name_by_room_id(room_id):
    try:
        room_inventory = await sync_to_async(RoomInventory.objects.get)(id=room_id)
        hotel_name = await sync_to_async(lambda: room_inventory.property.hotel_nick_name)()
        return hotel_name
    except Exception as e:
        return str(e)

async def get_owner_name_by_room_id(room_id):
    try:
        room_inventory = await sync_to_async(RoomInventory.objects.get)(id=room_id)
        owner_name = await sync_to_async(lambda: room_inventory.property.owner.hotel_name)()
        return owner_name
    except Exception as e:
        return str(e)

async def handle_customer_stop(websocket, session_id: str):
    await update_is_open(session_id)
    # Disconnect all owners associated with the session
    if session_id in active_rooms:
        if 'session_connections' in active_rooms[session_id]:
            for connection in active_rooms[session_id]['session_connections']:
                await connection.send_text("The session has been closed by the customer.")
                await manager.disconnect(connection, session_id)
        await manager.disconnect(websocket, session_id)
        # Remove the session from the active_rooms dictionary
        del active_rooms[session_id]

async def get_all_quotes_for_session(session_id):
    try:
        # Call the synchronous function using sync_to_async
        quotes = await get_all_quotes_for_session_sync(session_id)
        return quotes
    except Exception as e:
        print(f"Error retrieving quotes for session {session_id}: {e}")
        return []

async def handle_finish_message(session_id: str, user_info: Customer, room_id: int, websocket: WebSocket):
    if isinstance(user_info, Customer):
        property_deal_id = await get_property_deal_id(session_id, room_id)
        if property_deal_id is not None:
            await update_property_deal_winning_bid_status(property_deal_id)
            await update_is_open(session_id)
            last_bid = await get_last_bidding_amount(property_deal_id)
            last_amount = last_bid['amount__min'] if last_bid['amount__min'] is not None else 0
            owner_id = await get_property_deal_owner_id(property_deal_id)
            hotel_name = await get_hotel_name_by_room_id(room_id)
            await manager.send_personal_message(
                f"You selected {hotel_name} and the price for that is {last_amount}.",
                id(websocket),
                user_info,
                session_id
            )
        else:
            await manager.send_personal_message("Property deal ID not found for the room ID.")

active_rooms = {}
room_deal_prices = {}
session_connections = {}

@app.websocket("/ws/room_connection")
async def room_connection(
    websocket: WebSocket,
    user_type: str = Query(None),
    session_id: str = Query(None),
    token: str = Query(None),
    room_ids: str = Query(None)
):
    user_info = await get_current_user(token, user_type)
    if not user_info:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    try:
        if isinstance(user_info, Customer):
            customer_socket_id = id(websocket)
            active_rooms.setdefault(session_id, {'customer_socket_ids': []})['customer_socket_ids'].append(customer_socket_id)
            await manager.connect(websocket)

        if session_id:
            if session_id in active_rooms and active_rooms[session_id]['customer_socket_ids']:
                if isinstance(user_info, Owner):
                    await manager.connect(websocket)
                    await manager.update_active_room(websocket, session_id)
                    await websocket.send_text(f"You are now connected to session {session_id}.")
                    message = f"Owner {user_info.hotel_name} entered the session."
                    try:
                        for customer_socket_id in active_rooms[session_id]['customer_socket_ids']:
                            await manager.send_personal_message(message, customer_socket_id, user_info, session_id)
                    except Exception as e:
                        print("Error sending message:", e)
                    
                    if 'session_connections' not in active_rooms[session_id]:
                        active_rooms[session_id]['session_connections'] = []
                    active_rooms[session_id]['session_connections'].append(websocket)
                else:
                    await websocket.close(code=1008, reason="Owner ID not found.")
            else:
                await websocket.close(code=1008, reason="Invalid Session ID or Session not found.")
        else:
            if room_ids:
                room_ids_list = [int(prop_id) for prop_id in room_ids.split(",")]
                if len(room_ids_list) > 5:
                    await websocket.send_text("It is not allowed to add more than 5 properties in the bidding.")
                    await websocket.close(code=1008, reason="Too many properties added")
                    return
                else:
                    customer_id = user_info.id
                    session_id = str(await create_bidding_session(customer_id))
                    if session_id == "You have already created one session.":
                        await websocket.send_text(session_id)
                        return
                    deal_prices = {}
                    for room_id in room_ids_list:
                        try:
                            room_inventory = await sync_to_async(RoomInventory.objects.get)(id=room_id)
                            owner_name = await get_owner_name_by_room_id(room_id)
                            hotel_name = await get_hotel_name_by_room_id(room_id)
                            room_deal_prices[room_id] = room_inventory.deal_price
                            deal_prices[room_id] = {
                                'owner': owner_name,
                                'hotel_name': hotel_name,
                                'amount': room_inventory.deal_price,
                                'room_id': room_id
                            }
                            deal_id = await create_property_deal(session_id, customer_id, room_id)

                            print(deal_id,"this is deal id")

                            await sync_to_async(BiddingAmount.objects.create)(
                                property_deal_id=deal_id,
                                amount=room_inventory.deal_price
                            )
                        except RoomInventory.DoesNotExist:
                            await websocket.send_text(f"Room with ID {room_id} not found.")
                            continue

                    # Move database interactions outside the loop
                    await manager.save_active_room(websocket, session_id)
                    active_rooms[session_id] = {
                        'customer_socket_ids': [id(websocket)],
                        'room_deal_prices': deal_prices
                    }
                    await websocket.send_text(f"Session ID: {session_id}")
                    await websocket.send_text("You are now connected to the session.")
                    # await websocket.send_text("Deal prices for the rooms:")
                    for room_id, info in deal_prices.items():
                        await websocket.send_text(f"Room ID: {info['room_id']}, Hotel Name: {info['hotel_name']}, Amount: {info['amount']}, Owner Name:{info['owner']}")

        try:
            while True:
                message = await websocket.receive_text()

                if message.strip().lower() == "stop" and isinstance(user_info, Customer):
                    await handle_customer_stop(websocket, session_id)
                    
                    break

                if message == "leave":
                    if isinstance(user_info, Owner):
                        await manager.disconnect(websocket, session_id)
                        for customer_socket_id in active_rooms[session_id]['customer_socket_ids']:
                            await manager.send_personal_message(
                                f"{user_info.hotel_name} left the bidding session.",
                                customer_socket_id,  # Send the message only to the customer
                                user_info,
                                session_id
                            )
                        return
                    else:
                        await websocket.send_text("You are not authorized to leave the session.")
                
                if message.strip().lower().startswith("finish") and isinstance(user_info, Customer):
                    parts = message.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        room_id = int(parts[1])
                        await handle_finish_message(session_id, user_info, room_id, websocket)
                        await handle_customer_stop(session_id)
                    else:
                        await websocket.send_text("Invalid message format. Please enter a valid room ID after 'finish'.")

                else:
                    if message.startswith("quote"):
                        # Split the message by spaces to extract the bidding amount and room ID
                        parts = message.split()
                        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                            bidding_amount = float(parts[1])
                            room_id = int(parts[2])

                            if bidding_amount >= 0:
                                # Get the property deal ID for the given room ID
                                property_deal_id = await get_property_deal_id(session_id, room_id)
                                if property_deal_id is not None:
                                    # Use sync_to_async to execute the database operation asynchronously
                                    await sync_to_async(BiddingAmount.objects.create)(
                                        property_deal_id=property_deal_id,
                                        amount=bidding_amount
                                    )
                                    # Retrieve all quotes for the session from the database
                                    all_quotes = await get_all_quotes_for_session(session_id)

                                    if all_quotes:
                                        # Sort the quotes in descending order of amount
                                        sorted_quotes = sorted(all_quotes, key=lambda x: x['amount'])

                                        # Prepare the message to be sent to the customer
                                        message_to_send = "Quotes received for the session:\n"
                                        for quote in sorted_quotes:
                                            room_id = quote['room_id']
                                            hotel_nick_name = quote['hotel_nick_name']
                                            amount = quote['amount']
                                            message_to_send += f"Room ID: {room_id}, Hotel name: {hotel_nick_name}, Amount: {amount}\n"
                                        
                                        # Send the message to each customer associated with the session
                                        for customer_socket_id in active_rooms[session_id]['customer_socket_ids']:
                                            await manager.send_personal_message(
                                                message_to_send,
                                                customer_socket_id,
                                                user_info,
                                                session_id
                                            )
                                        
                                        is_lowest_quote = True
                                        for quote in all_quotes:
                                            if quote['amount'] < bidding_amount:
                                                is_lowest_quote = False
                                                break
                                        
                                        if is_lowest_quote:
                                            await manager.send_personal_message(
                                                f"Your are winning the bid.",
                                                id(websocket),  # Send the message to the owner
                                                user_info,
                                                session_id
                                            )

                                            # Inform other owners about their status
                                            for owner_socket in active_rooms[session_id]['session_connections']:
                                                owner_socket_id = id(owner_socket)
                                                if owner_socket_id != id(websocket):
                                                    await manager.send_personal_message(
                                                        f"You are Losing the bid.",
                                                        owner_socket_id,
                                                        user_info,
                                                        session_id
                                                    )
                                        
                                        else:
                                            await manager.send_personal_message(
                                                f"You are Losing the bid.",
                                                id(websocket),  # Send the message to the owner
                                                user_info,
                                                session_id
                                            )

                                        # Send confirmation message to the owner
                                        await manager.send_personal_message(
                                            f"Your bid of {bidding_amount} for room {room_id} has been successfully sent.",
                                            id(websocket),  # Send the message to the owner
                                            user_info,
                                            session_id
                                        )
                                else:
                                    await websocket.send_text("Property deal ID not found for the room ID.")
                            else:
                                await websocket.send_text("Invalid bidding amount. Please enter a non-negative number.")
                        else:
                            await websocket.send_text("Invalid message format. Please enter a message in the format 'quote <amount> <room_id>'.")
                    else:
                        await websocket.send_text("Invalid message format. Please enter a valid bidding amount.")
        
        except WebSocketDisconnect:
            await manager.disconnect(websocket, session_id)
                 
    except Exception as e:
        print("An error occurred during websocket connection handling:")
        print(repr(e))


if __name__ == '__main__':
    uvicorn.run("websocket:app", host="0.0.0.0", port=7000, log_level="info", reload=True)
