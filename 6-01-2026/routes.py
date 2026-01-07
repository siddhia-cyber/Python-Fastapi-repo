from fastapi import APIRouter, HTTPException
from models import User, UpdateUser
from database import collection
from bson import ObjectId

router = APIRouter()

@router.get("/")
def root():
    return {"message": "FastAPI is running"}

@router.post("/users")
def create_user(user: User):
    result = collection.insert_one(user.dict())
    return {"id": str(result.inserted_id)}

@router.get("/users")
def get_users():
    users = []
    for user in collection.find():
        user["_id"] = str(user["_id"])
        users.append(user)
    return users

@router.get("/users/{user_id}")
def get_user(user_id: str):
    user = collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return user

@router.put("/users/{user_id}")
def update_user(user_id: str, user: UpdateUser):
    updated = collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {k: v for k, v in user.dict().items() if v is not None}}
    )

    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated"}

@router.delete("/users/{user_id}")
def delete_user(user_id: str):
    deleted = collection.delete_one({"_id": ObjectId(user_id)})

    if deleted.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted"}