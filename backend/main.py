from database.connection import MongoDBConnection
from services.accounts_service import AccountsService
from services.users_service import UsersService
from encoder.json_encoder import MyJSONEncoder

import logging

from typing import List, Dict

import json
from bson import ObjectId
from pydantic import BaseModel

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


class FetchAccountsResponse(BaseModel):
    accounts: List[Dict]


@app.post("/fetch-accounts", response_model=FetchAccountsResponse)
async def fetch_accounts():
    """Retrieve all accounts, optionally excluding a specific account.
    Args:
        request (Request): The request object containing an optional account_id to exclude.
    Returns:
        dict: A list of all accounts, optionally excluding a specific account.
    """
    try:
        # Directly fetch all accounts without exclusion logic
        accounts = accounts_service.get_accounts()
        logging.info(f"Retrieved {len(accounts)} accounts from the database")

        return Response(content=json.dumps({"accounts": accounts}, cls=MyJSONEncoder), media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-active-accounts", response_model=FetchAccountsResponse)
async def fetch_active_accounts():
    """Retrieve all active accounts, optionally excluding a specific account.
    Args:
        request (Request): The request object containing an optional account_id to exclude.
    Returns:
        dict: A list of all active accounts, optionally excluding a specific account.
    """
    try:
        # Directly fetch all active accounts without exclusion logic
        accounts = accounts_service.get_active_accounts()
        logging.info(
            f"Retrieved {len(accounts)} active accounts from the database")

        return Response(content=json.dumps({"accounts": accounts}, cls=MyJSONEncoder), media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving active accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class FindAccountByNumberRequest(BaseModel):
    account_number: str


class FindAccountByNumberResponse(BaseModel):
    account: Dict


@app.post("/find-account-by-number", response_model=FindAccountByNumberResponse)
async def find_account_by_number(request: Request, account_data: FindAccountByNumberRequest):
    """Retrieve an account by its number.
    Args:
        request (Request): The request object containing the account number.
    Returns:
        dict: The account document if found, otherwise an error message.
    """
    try:
        data = await request.json()
        account_number = data.get("account_number")

        if account_number is None:
            raise HTTPException(
                status_code=400, detail="Account number is required")

        # Ensure account_number is treated as a string
        account_number = str(account_number)

        account = accounts_service.get_account_by_number(account_number)
        if account:
            logging.info(f"Found account with number {account_number}")
            return Response(content=json.dumps({"account": account}, cls=MyJSONEncoder), media_type="application/json")
        else:
            logging.info(f"No account found with number {account_number}")
            raise HTTPException(status_code=404, detail="Account not found")

    except Exception as e:
        logging.error(f"Error retrieving account by number: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/find-active-account-by-number", response_model=FindAccountByNumberResponse)
async def find_active_account_by_number(request: Request, account_data: FindAccountByNumberRequest):
    """Retrieve an active account by its number.
    Args:
        request (Request): The request object containing the account number.
    Returns:
        dict: The account document if found, otherwise an error message.
    """
    try:
        data = await request.json()
        account_number = data.get("account_number")

        if account_number is None:
            raise HTTPException(
                status_code=400, detail="Account number is required")

        # Ensure account_number is treated as a string
        account_number = str(account_number)

        account = accounts_service.get_active_account_by_number(account_number)
        if account:
            logging.info(f"Found active account with number {account_number}")
            return Response(content=json.dumps({"account": account}, cls=MyJSONEncoder), media_type="application/json")
        else:
            logging.info(
                f"No active account found with number {account_number}")
            raise HTTPException(
                status_code=404, detail="Active account not found")

    except Exception as e:
        logging.error(f"Error retrieving active account by number: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


class CreateAccountRequest(BaseModel):
    UserName: str
    UserId: str
    AccountNumber: str
    AccountBalance: float
    AccountType: str


class CreateAccountResponse(BaseModel):
    message: str
    account_id: str


@app.post("/create-account", response_model=CreateAccountResponse)
async def create_account(request: Request, account_data: CreateAccountRequest):
    """Create a new account with the provided data.

    Args:
        request (Request): The request object containing account data.
        account_data (AccountRequest): The account data to create a new account.

    Returns:
        AccountResponse: A dictionary indicating success with the created account ID.
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

        # Validate account balance constraints
        if account_balance < 0:
            raise HTTPException(
                status_code=400, detail="Account balance must be greater than or equal to 0.")

        initial_balance_limit = float(1000000)
        if account_balance > initial_balance_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Account balance exceeds the limit of {initial_balance_limit}.")

        # Check for duplicate account number before creation
        if accounts_service.accounts_collection.find_one({"AccountNumber": account_number}):
            raise HTTPException(
                status_code=400, detail="An account with this number already exists.")

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

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        logging.error(f"HTTP error creating account: {str(he)}")
        raise he
    except Exception as e:
        logging.error(f"Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


class CloseAccountRequest(BaseModel):
    account_id: str


class CloseAccountResponse(BaseModel):
    message: str


@app.post("/close-account", response_model=CreateAccountResponse)
async def close_account(request: Request, account_data: CloseAccountRequest):
    """
    Close an account by its ID: account_id if the balance is zero.

    Args:
        request (Request): The request object containing account data.
        account_data (CreateAccountRequest): The account data to create a new account.

    Returns:
        CreateAccountResponse: A dictionary indicating success with the created account ID.
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
            return {"account_id": account_id, "message": "Account closed successfully"}
        else:
            logging.error(f"Account with ID {account_id} cannot be closed")
            raise HTTPException(
                status_code=400, detail="Account cannot be closed")
    except Exception as e:
        logging.error(f"Error closing account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class FetchAccountsForUserRequest(BaseModel):
    user_identifier: str


@app.post("/fetch-accounts-for-user", response_model=FetchAccountsResponse)
async def fetch_accounts_for_user(request: Request, user_data: FetchAccountsForUserRequest):
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


@app.post("/fetch-active-accounts-for-user", response_model=FetchAccountsResponse)
async def fetch_active_accounts_for_user(request: Request, user_data: FetchAccountsForUserRequest):
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


class FetchUsersResponse(BaseModel):
    users: List[Dict]


@app.post("/fetch-users", response_model=FetchUsersResponse)
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


class FindUserRequest(BaseModel):
    user_identifier: str


class FindUserResponse(BaseModel):
    user: Dict


@app.post("/find-user", response_model=FindUserResponse)
async def find_user(request: Request, user_data: FindUserRequest):
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
