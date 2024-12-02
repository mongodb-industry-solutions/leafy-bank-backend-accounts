from bson import ObjectId
from datetime import datetime
from database.connection import MongoDBConnection
from services.account_service import AccountService
import logging
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_account(account_service: AccountService, account_data: dict) -> ObjectId:
    """Create an account and return its ID."""
    try:
        account_id = account_service.create_account(account_data)
        logging.info(f"Account created with ID: {account_id}")
        return account_id
    except Exception as e:
        logging.error(f"Failed to create account: {e}")
        return None

def delete_account(account_service: AccountService, account_id: ObjectId):
    """Delete an account by its ID."""
    if account_id is None:
        logging.error("No account ID provided for deletion.")
        return

    try:
        success = account_service.delete_account(str(account_id))
        if success:
            logging.info(f"Account with ID {account_id} deleted successfully.")
        else:
            logging.error(f"Failed to delete account with ID {account_id}.")
    except Exception as e:
        logging.error(f"Failed to delete account: {e}")

def main():
    # Initialize the MongoDB connection
    uri = MONGODB_URI
    db_name = "leafy_bank"
    accounts_collection_name = "accounts"
    users_collection_name = "users"
    connection = MongoDBConnection(uri)

    # Initialize the AccountService
    account_service = AccountService(connection, db_name, accounts_collection_name, users_collection_name)

    # Sample account data
    account_data = {
        "_id": ObjectId(),  # Generate a new unique ObjectId
        "AccountNumber": "5555555555",
        "AccountBank": "LeafyBank",
        "AccountStatus": "Active",
        "AccountIdentificationType": "AccountNumber",
        "AccountDate": {
            "OpeningDate": datetime(2024, 12, 2)
        },
        "AccountType": "Checking",
        "AccountBalance": float(1000),  # Ensure this is a float
        "AccountCurrency": "EUR",
        "AccountDescription": "New checking account",
        "AccountUser": {
            "UserName": "fridaklo",
            "UserId": ObjectId("65a546ae4a8f64e8f88fb89e")
        }
    }

    # Create an account
    account_id = create_account(account_service, account_data)

    # Delete the account
    delete_account(account_service, account_id)

if __name__ == "__main__":
    main()
