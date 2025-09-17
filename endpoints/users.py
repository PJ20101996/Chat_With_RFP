from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import hashlib

# Local imports
from models.models import TokenSchema as Token  # Keep for Pydantic schema use
from db.database import get_connection
from app.utils import create_access_token, decode_access_token

router = APIRouter(
    prefix="/job_analysis",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

# Add single user endpoint with JWT authentication
@router.post("/user/adduser", responses={200: {"headers": {"Access-Control-Allow-Origin": "*"}}})
async def add_single_user(
    request: Request,
    authorization: str = Header(None)  # Expecting 'Bearer <token>'
):
    #  Check JWT token
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_access_token(token)
    if decoded.get("status") == "error":
        raise HTTPException(
            status_code=decoded["status_code"],
            detail=decoded["detail"]
        )
    async with get_connection() as (cursor, conn):
        data = await request.json()

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
        existing_user = cursor.fetchone()
        if existing_user:
            return JSONResponse(
                status_code=200,
                content={"status_code": 200, "message": "success", "details": "User already exists !!"}
            )

        # Hash the password
        password_hashed = hashlib.md5(data['password'].encode('utf-8')).hexdigest()

        # Insert user into users table
        cursor.execute(
            """
            INSERT INTO users (name, email, password, companyId, roleId, changePrompt, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (data['name'], data['email'], password_hashed, data['companyId'], data['roleId'], data['changePrompt'], data['status'])
        )
        conn.commit()

        # Get the inserted user's id
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        user_id = cursor.fetchone()['id']

        # Inserting  user prompts 
        for prompt in data.get('prompts', []):
            cursor.execute(
                """
                INSERT INTO user_prompts (promptName, promptDescription, userId, status)
                VALUES (%s, %s, %s, %s)
                """,
                (prompt['promptName'], prompt['promptDescription'], user_id, prompt['status'])
            )
        conn.commit()

        return JSONResponse(
            status_code=200,
            content={"status_code": 200, "message": "User Added Successfully"}
        )
@router.post("/user/login")
async def login_user(request: Request):
    data = await request.json()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Checking if user exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (data["email"],))
            record = cursor.fetchone()

            if not record:
                raise HTTPException(status_code=404, detail={"status": 404, "message": "User not found"})

            #  Verifying password
            password = hashlib.md5(data['password'].encode('utf-8')).hexdigest()
            if password != record["password"]:
                return JSONResponse(
                    status_code=401,
                    content={"status_code": 401, "message": "Wrong password"}
                )

            #  Get company details
            cursor.execute("SELECT id, companyName FROM company WHERE id = %s", (record["companyId"],))
            company_details = cursor.fetchone()

            #  Get role details
            cursor.execute("SELECT id, roleName FROM role WHERE id = %s", (record["roleId"],))
            role_details = cursor.fetchone()

        # Add extra data
        record["companysData"] = company_details
        record["rolesData"] = role_details

    finally:
        conn.close()

    # Generate JWT token
    token = {
        "access_token": create_access_token(data["email"]),
        "token_type": "Bearer"
    }

    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "success",
            "user": record,
            "token_type": token["token_type"],
            "access_token": token["access_token"]
        }
    )
#  Update User
@router.put("/user/updateuser", responses={200: {"headers": {"Access-Control-Allow-Origin": "*"}}})
async def update_user(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_access_token(token)
    if decoded.get("status") == "error":
        raise HTTPException(status_code=decoded["status_code"], detail=decoded["detail"])

    data = await request.json()
    user_id = data.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID missing")

    prompts = data.pop("prompts", [])
    if "password" in data and data["password"]:
        data["password"] = hashlib.md5(data["password"].encode("utf-8")).hexdigest()

    async with get_connection() as (cursor, conn):
        # Update user
        update_fields = ", ".join([f"{k} = %s" for k in data.keys()])
        cursor.execute(
            f"UPDATE users SET {update_fields} WHERE id = %s",
            (*data.values(), user_id),
        )
        conn.commit()

        # Replace user prompts
        cursor.execute("DELETE FROM user_prompts WHERE userId = %s", (user_id,))
        for p in prompts:
            cursor.execute(
                """
                INSERT INTO user_prompts (promptName, promptDescription, userId, status)
                VALUES (%s, %s, %s, %s)
                """,
                (p["promptName"], p["promptDescription"], user_id, p.get("status", 1)),
            )
        conn.commit()

    return JSONResponse(status_code=200, content={"status_code": 200, "message": "User Updated Successfully"})


#  Delete User (soft delete)
@router.put("/user/deleteuser/{id}", responses={200: {"headers": {"Access-Control-Allow-Origin": "*"}}})
async def delete_user(id: int, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_access_token(token)
    if decoded.get("status") == "error":
        raise HTTPException(status_code=decoded["status_code"], detail=decoded["detail"])

    async with get_connection() as (cursor, conn):
        cursor.execute("UPDATE users SET status = 0 WHERE id = %s", (id,))
        conn.commit()

    return JSONResponse(status_code=200, content={"status_code": 200, "message": "User Deleted Successfully"})


#  Get current user (from JWT)
@router.post("/user/me", responses={200: {"headers": {"Access-Control-Allow-Origin": "*"}}})
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_access_token(token)

    if decoded.get("status") == "error":
        return JSONResponse(
            status_code=decoded["status_code"],
            content={"status_code": decoded["status_code"], "message": "failed", "data": decoded},
        )

    return JSONResponse(
        status_code=200,
        content={"status_code": 200, "message": "success", "data": decoded["data"]},
    )


#  Get all active users of a company
@router.get("/user/getallusers/{companyId}", responses={200: {"headers": {"Access-Control-Allow-Origin": "*"}}})
async def get_all_users(companyId: int, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_access_token(token)
    if decoded.get("status") == "error":
        raise HTTPException(status_code=decoded["status_code"], detail=decoded["detail"])

    async with get_connection() as (cursor, conn):
        # Users
        cursor.execute("SELECT * FROM users WHERE companyId = %s AND status = 1", (companyId,))
        users = cursor.fetchall()

        # Prompts
        cursor.execute("SELECT * FROM user_prompts")
        prompts = cursor.fetchall()

        # Roles
        cursor.execute("SELECT * FROM role")
        roles = cursor.fetchall()

        # Profile Matches
        cursor.execute("SELECT * FROM profile_match")
        matches = cursor.fetchall()

    role_map = {r["id"]: r["roleName"] for r in roles}
    user_prompts = {}
    for p in prompts:
        user_prompts.setdefault(p["userId"], []).append(
            {"id": p["id"], "promptName": p["promptName"], "promptDescription": p["promptDescription"]}
        )

    match_map = {}
    for m in matches:
        uid = m["userId"]
        match_map.setdefault(uid, []).append(m)

    users_list = []
    for u in users:
        u["roleName"] = role_map.get(u["roleId"], "")
        u["prompts"] = user_prompts.get(u["id"], [])
        user_matches = match_map.get(u["id"], [])
        u["total_resume_parsed"] = len(user_matches)
        u["totalTokenUsed"] = sum(m["totalTokenUsed"] for m in user_matches)
        u["totalCost"] = sum(m["totalCost"] for m in user_matches)
        users_list.append(u)

    return JSONResponse(status_code=200, content={"status_code": 200, "message": "success", "users_list": users_list})


#  Get all inactive users
@router.get("/user/getallinactiveusers", responses={200: {"headers": {"Access-Control-Allow-Origin": "*"}}})
async def get_all_inactive_users(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    decoded = decode_access_token(token)
    if decoded.get("status") == "error":
        raise HTTPException(status_code=decoded["status_code"], detail=decoded["detail"])

    async with get_connection() as (cursor, conn):
        # Users
        cursor.execute("SELECT * FROM users WHERE status = 0")
        users = cursor.fetchall()

        # Prompts
        cursor.execute("SELECT * FROM user_prompts")
        prompts = cursor.fetchall()

        # Roles
        cursor.execute("SELECT * FROM role")
        roles = cursor.fetchall()

        # Profile Matches
        cursor.execute("SELECT * FROM profile_match")
        matches = cursor.fetchall()

    role_map = {r["id"]: r["roleName"] for r in roles}
    user_prompts = {}
    for p in prompts:
        user_prompts.setdefault(p["userId"], []).append(
            {"id": p["id"], "promptName": p["promptName"], "promptDescription": p["promptDescription"]}
        )

    match_map = {}
    for m in matches:
        match_map.setdefault(m["userId"], []).append(m)

    users_list = []
    for u in users:
        u["roleName"] = role_map.get(u["roleId"], "")
        u["prompts"] = user_prompts.get(u["id"], [])
        u["total_resume_parsed"] = len(match_map.get(u["id"], []))
        users_list.append(u)

    return JSONResponse(status_code=200, content={"status_code": 200, "message": "success", "inactive_users_list": users_list})

