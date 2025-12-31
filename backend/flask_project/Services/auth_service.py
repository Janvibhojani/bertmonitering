# # services/auth_service.py
# import jwt
# import os
# from Services.url_Service import fetch_user_allocated_urls

# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
# HASH_ALGORITHM = os.getenv("HASH_ALGORITHM", "HS256")

# def authenticate_user(sio, sid, data, authenticated_clients):
#     token = data.get("token")

#     if not token:
#         sio.emit("status", {"error": "Token missing!"}, to=sid)
#         return False

#     try:
#         payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[HASH_ALGORITHM])
#         user_id = payload.get("user_id") or payload.get("id")
#         role = payload.get("role","user")
        
#         authenticated_clients[sid] = {
#             "user_id": user_id,
#             "role": role
#         }

#         if not user_id:
#             raise jwt.InvalidTokenError("user_id missing")

#         sio.enter_room(sid, role) #admin/user role room
#         sio.enter_room(sid, str(user_id)) #individual user room
#         allocated = fetch_user_allocated_urls(user_id)
#         for url_info in allocated:
#             url_id = url_info.get("_id")
#             if url_id:
#                 sio.enter_room(sid, f"url:{url_id}")
#         sio.emit("status", {
#             "status": "authenticated",
#             "message": f"Authenticated as user {role} {user_id}"
#         }, to=sid)

#         return True

#     except jwt.ExpiredSignatureError:
#         sio.emit("status", {"error": "Token expired!"}, to=sid)
#     except jwt.InvalidTokenError as e:
#         sio.emit("status", {"error": f"Invalid token: {str(e)}"}, to=sid)

#     return False
# # services/auth_service.py
import jwt
import os
from Services.url_Service import fetch_user_allocated_urls

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
HASH_ALGORITHM = "HS256"
authenticated_clients = {}
def authenticate_user(sio, sid, data, authenticated_clients):
    token = data.get("token")

    if not token:
        sio.emit("status", {"error": "Token missing"}, to=sid)
        return False

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[HASH_ALGORITHM])

        user_id = payload.get("user_id") or payload.get("id")
        role = payload.get("role", "user")

        if not user_id:
            raise jwt.InvalidTokenError("user_id missing")

        user_id = str(user_id)

        # ✅ save authenticated client
        authenticated_clients[sid] = {
            "user_id": user_id,
            "role": role
        }

        # 👤 personal room
        sio.enter_room(sid, f"user:{user_id}")
        if role == "admin":
            sio.enter_room(sid, "admin")
        # 🔗 url-based rooms
        allocated_urls = fetch_user_allocated_urls(user_id)

        for url in allocated_urls:

            # case 1: url is string
            if isinstance(url, str):
                url_id = url

            # case 2: url is dict
            elif isinstance(url, dict):
                url_id = url.get("_id") or url.get("url_id")

            else:
                continue

            if url_id:
                sio.enter_room(sid, f"url:{url_id}")

        sio.emit(
            "status",
            {
                "status": "authenticated",
                "role": role,
                "user_id": user_id
            },
            to=sid
            
        )
        return True
    

    except jwt.ExpiredSignatureError:
        sio.emit("status", {"error": "Token expired"}, to=sid)

    except jwt.InvalidTokenError as e:
        sio.emit("status", {"error": f"Invalid token: {str(e)}"}, to=sid)

    return False

