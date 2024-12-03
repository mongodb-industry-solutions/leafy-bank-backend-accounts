from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import os
from dotenv import load_dotenv

load_dotenv()

from database.connection import MongoDBConnection
from backend.services.accounts_service import AccountService
from bson import ObjectId

MONGODB_URI = os.getenv("MONGODB_URI")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Initialize the MongoDB connection
uri = MONGODB_URI
db_name = "leafy_bank"
accounts_collection_name = "accounts"
users_collection_name = "users"
connection = MongoDBConnection(uri)

# Initialize the AccountService
account_service = AccountService(connection, db_name, accounts_collection_name, users_collection_name)

@app.get("/")
async def read_root(request: Request):
    return {"message":"Server is running"}

@app.post("/create-account/")
async def create_account(request: Request):
    try:
        # Parse the incoming JSON data
        account_data = await request.json()
        # Convert UserId to ObjectId
        account_data["AccountUser"]["UserId"] = ObjectId(account_data["AccountUser"]["UserId"])
        
        # Create the account
        account_id = account_service.create_account(account_data)
        return {"account_id": str(account_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {e}")