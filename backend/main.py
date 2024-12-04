from database.connection import MongoDBConnection
from services.accounts_service import AccountsService
from services.users_service import UsersService
from encoder.json_encoder import MyJSONEncoder

import logging

import json
from bson import ObjectId

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

MONGODB_URI = os.getenv("MONGODB_URI")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Initialize the MongoDB connection
db_name = "leafy_bank"
accounts_collection_name = "accounts"
users_collection_name = "users"
connection = MongoDBConnection(MONGODB_URI)

# Initialize the AccountService
accounts_service = AccountsService(
    connection, db_name, accounts_collection_name, users_collection_name)

# Initialize the UsersService
users_service = UsersService(connection, db_name, users_collection_name)


@app.get("/")
async def read_root(request: Request):
    return {"message": "Server is running"}


@app.post("/create-account")
async def create_account(request: Request):
    """Create a new account with the provided data.
    Args:
        request (Request): The request object containing account data.
    Returns:
        dict: A message indicating success and the account ID.
    """
    try:
        data = await request.json()

        # Extract required fields from the request data
        user_name = data.get("UserName")
        user_id = data.get("UserId")
        account_number = data.get("AccountNumber")
        account_balance = data.get("AccountBalance")
        account_type = data.get("AccountType")

        # Validate required fields
        if not all([user_name, user_id, account_number, account_balance, account_type]):
            raise HTTPException(
                status_code=400, detail="Missing required account data")

        # Validate account balance is a float
        try:
            account_balance = float(account_balance)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Account balance must be a valid number.")
        # Validate account balance is greater than or equal to 0
        if account_balance < 0:
            raise HTTPException(
                status_code=400, detail="Account balance must be greater than or equal to 0.")

        # Validate account balance does not exceed the limit
        # Set the initial balance limit to 1M
        initial_balance_limit = float(1000000)
        if account_balance > initial_balance_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Account balance exceeds the limit of {initial_balance_limit}. Please ensure the balance is {initial_balance_limit} or less."
            )

        # Create the account using the refactored function
        account_id = accounts_service.create_account(
            user_name=user_name,
            user_id=user_id,
            account_number=account_number,
            account_balance=account_balance,
            account_type=account_type
        )
        logging.info(f"Account created with ID {account_id}")
        return {"message": "Account created successfully", "account_id": str(account_id)}
    except Exception as e:
        logging.error(f"Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delete-account")
async def delete_account(request: Request):
    """Delete an account by its ID: account_id.
    Args:
        request (Request): The request object containing the account ID.
    Returns:
        dict: A message indicating success or failure.
    """
    try:
        data = await request.json()
        account_id = data.get("account_id")
        if not account_id or not ObjectId.is_valid(account_id):
            raise HTTPException(
                status_code=400, detail="Invalid account ID format")
        success = accounts_service.delete_account(account_id)
        if success:
            logging.info(f"Account with ID {account_id} deleted successfully")
            return {"message": "Account deleted successfully"}
        else:
            logging.error(f"Account with ID {account_id} not found")
            raise HTTPException(status_code=404, detail="Account not found")
    except Exception as e:
        logging.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/close-account")
async def close_account(request: Request):
    """Close an account by its ID: account_id if the balance is zero.
    Args:
        request (Request): The request object containing the account ID.
    Returns:
        dict: A message indicating success or failure.
    """
    try:
        data = await request.json()
        account_id = data.get("account_id")
        if not account_id or not ObjectId.is_valid(account_id):
            raise HTTPException(
                status_code=400, detail="Invalid account ID format")
        success = accounts_service.close_account(account_id)
        if success:
            logging.info(f"Account with ID {account_id} closed successfully")
            return {"message": "Account closed successfully"}
        else:
            logging.error(f"Account with ID {account_id} cannot be closed")
            raise HTTPException(
                status_code=400, detail="Account cannot be closed")
    except Exception as e:
        logging.error(f"Error closing account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-accounts-for-user")
async def fetch_accounts_for_user(request: Request):
    """Retrieve all accounts for a specific user by UserName or ID.
    Args:
        request (Request): The request object containing the user_identifier.
    Returns:
        dict: A list of accounts associated with the user.
    """
    try:
        data = await request.json()
        user_identifier = data.get("user_identifier")
        if not user_identifier:
            raise HTTPException(
                status_code=400, detail="User identifier is required")
        if ObjectId.is_valid(user_identifier):
            user_identifier = ObjectId(user_identifier)
        accounts = accounts_service.get_accounts_for_user(user_identifier)
        if accounts:
            logging.info(
                f"Found {len(accounts)} accounts for user {user_identifier}")
            return Response(content=json.dumps({"accounts": accounts}, cls=MyJSONEncoder), media_type="application/json")
        else:
            logging.info(f"No accounts found for user {user_identifier}")
            return Response(content=json.dumps({"accounts": []}, cls=MyJSONEncoder), media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving accounts for user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-active-accounts-for-user")
async def fetch_active_accounts_for_user(request: Request):
    """Retrieve active accounts for a specific user by UserName or ID.
    Args:
        request (Request): The request object containing the user_identifier.
    Returns:
        dict: A list of active accounts associated with the user.
    """
    try:
        data = await request.json()
        user_identifier = data.get("user_identifier")
        if not user_identifier:
            raise HTTPException(
                status_code=400, detail="User identifier is required")
        if ObjectId.is_valid(user_identifier):
            user_identifier = ObjectId(user_identifier)
        accounts = accounts_service.get_active_accounts_for_user(
            user_identifier)
        if accounts:
            logging.info(
                f"Found {len(accounts)} active accounts for user {user_identifier}")
            return Response(content=json.dumps({"accounts": accounts}, cls=MyJSONEncoder), media_type="application/json")
        else:
            logging.info(
                f"No active accounts found for user {user_identifier}")
            return Response(content=json.dumps({"accounts": []}, cls=MyJSONEncoder), media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving active accounts for user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-users")
async def fetch_users():
    """Retrieve all users from the database.
    Returns:
        dict: A list of all users.
    """
    try:
        users = users_service.get_users()
        logging.info(f"Retrieved {len(users)} users from the database")
        return Response(content=json.dumps({"users": users}, cls=MyJSONEncoder), media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-user")
async def fetch_user(request: Request):
    """Retrieve a specific user by UserName or ID.
    Args:
        request (Request): The request object containing the user_identifier.
    Returns:
        dict: The user document if found, otherwise an error message.
    """
    try:
        data = await request.json()
        user_identifier = data.get("user_identifier")
        if not user_identifier:
            raise HTTPException(
                status_code=400, detail="User identifier is required")
        if ObjectId.is_valid(user_identifier):
            user_identifier = ObjectId(user_identifier)
        user = users_service.get_user(user_identifier)
        if user:
            logging.info(f"User found with ID {user['_id']}")
            return Response(content=json.dumps({"user": user}, cls=MyJSONEncoder), media_type="application/json")
        else:
            logging.info(f"No user found with identifier {user_identifier}")
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logging.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
