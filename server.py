from flask import Flask, request
from flask_socketio import SocketIO, join_room, emit
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Example: { "room_id": [ {"id": "player_id", "name": "player_name", "vote": None, "isModerator"?: True}, {"id": "player_id", "name": "player_name", "vote": None, "isModerator": False"} ] }
rooms = {}  # Dictionary to hold room information

@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


import uuid
from flask_socketio import emit, join_room

# Handle creating a new room and generating userId
@socketio.on("create_room")
def handle_create_room(data):
    username = data.get("username")
    if not username:
        return {"success": False, "error": "Username is required"}

    room_id = str(uuid.uuid4())[:8]  # Generate unique room ID
    user_id = str(uuid.uuid4())  # Generate unique user ID for the new player

    # Initialize room with the first player
    rooms[room_id] = [{"id": user_id, "name": username, "vote": None, "isModerator": True}]
    join_room(room_id)

    # Send back the room ID and user ID
    emit("room_created", {"roomId": room_id, "userId": user_id}, room=request.sid)
    print(f"Room created: {room_id} by {username}, userId: {user_id}")
    return {"roomId": room_id, "userId": user_id, "isModerator":True}


@socketio.on("join_room")
def handle_join_room(data):
    room_id = data.get("roomId")
    username = data.get("username")
    if not room_id or not username:
        return {"success": False, "error": "Room ID and username are required"}

    if room_id in rooms:
        player_id = str(uuid.uuid4())
        rooms[room_id].append({"id": player_id, "name": username, "vote": None})
        join_room(room_id)
        emit("player_joined", {"players": rooms[room_id]}, room=room_id)
        print(f"User {username} joined room: {room_id}")
        return {"success": True, "userId": player_id}
    else:
        return {"success": False, "error": "Room does not exist"}


@socketio.on("get_players")
def handle_get_players(data):
    room_id = data.get("roomId")
    if not room_id or room_id not in rooms:
        return {"success": False, "error": "Room does not exist"}
    
    # Send back the player list
    emit("player_list", {"players": rooms[room_id]}, room=request.sid)
    
@socketio.on("vote")
def handle_vote(data):
    room_id = data.get("roomId")
    player_id = data.get("playerId")
    vote = data.get("vote")

    if room_id in rooms:
        for player in rooms[room_id]:
            if player["id"] == player_id:
                player["vote"] = vote
                break
        emit("player_voted", {"players": rooms[room_id]}, room=room_id)
        print(f"Player {player_id} voted {vote} in room {room_id}")
    else:
        emit("error", {"message": "Room does not exist"}, to=request.sid)


@socketio.on("reveal_votes")
def handle_reveal_votes(data):
    room_id = data.get("roomId")

    if room_id in rooms:
        emit("votes_revealed", room=room_id)
        print(f"Votes revealed in room {room_id}")
    else:
        emit("error", {"message": "Room does not exist"}, to=request.sid)


@socketio.on("reset_round")
def handle_reset_round(data):
    room_id = data.get("roomId")

    if room_id in rooms:
        for player in rooms[room_id]:
            player["vote"] = None
        emit("round_reset", room=room_id)
        print(f"Round reset in room {room_id}")
    else:
        emit("error", {"message": "Room does not exist"}, to=request.sid)


@socketio.on("check_moderator")
def handle_check_moderator(data):
    room_id = data.get("roomId")

    if room_id in rooms:
        is_moderator = rooms[room_id][0]["isModerator"]
        return {"isModerator": is_moderator}
        emit("moderator_status", {"isModerator": is_moderator}, to=request.sid)
    else:
        emit("error", {"message": "Room does not exist"}, to=request.sid)


if __name__ == "__main__":
    print("Starting server...")
    socketio.run(app, host="0.0.0.0", port=5000)
