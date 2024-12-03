from bson import ObjectId
from datetime import datetime
from database.connection import MongoDBConnection
from services.accounts_service import AccountsService

import logging
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_account(account_service: AccountsService, account_data: dict) -> ObjectId:
    """Create an account and return its ID."""
    try:
        account_id = account_service.create_account(account_data)
        logging.info(f"Account created with ID: {account_id}")
        return account_id
    except Exception as e:
        logging.error(f"Failed to create account: {e}")
        return None


def delete_account(account_service: AccountsService, account_id: ObjectId):
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


def get_accounts_for_user(account_service: AccountsService, user_identifier):
    """Retrieve and log accounts for a specific user."""
    try:
        accounts = account_service.get_accounts_for_user(user_identifier)
        if accounts:
            logging.info(f"Accounts for user {user_identifier}:")
            for account in accounts:
                logging.info(account)
        else:
            logging.info(f"No accounts found for user {user_identifier}.")
    except Exception as e:
        logging.error(f"Failed to retrieve accounts for user {user_identifier}: {e}")

def close_account(account_service: AccountsService, account_id: ObjectId):
    """Attempt to close an account by its ID."""
    if account_id is None:
        logging.error("No account ID provided for closing.")
        return
    try:
        success = account_service.close_account(str(account_id))
        if success:
            logging.info(f"Account with ID {account_id} closed successfully.")
        else:
            logging.error(f"Failed to close account with ID {account_id}.")
    except Exception as e:
        logging.error(f"Failed to close account: {e}")


def main():
    # Initialize the MongoDB connection
    uri = MONGODB_URI
    db_name = "leafy_bank"
    accounts_collection_name = "accounts"
    users_collection_name = "users"
    connection = MongoDBConnection(uri)

    # Initialize the AccountsService
    account_service = AccountsService(connection, db_name, accounts_collection_name, users_collection_name)

    # # Sample account data
    # account_data = {
    #     "_id": ObjectId(),  # Generate a new unique ObjectId
    #     "AccountNumber": "666552219",
    #     "AccountBank": "LeafyBank",
    #     "AccountStatus": "Active",
    #     "AccountIdentificationType": "AccountNumber",
    #     "AccountDate": {
    #         "OpeningDate": datetime(2024, 12, 3)
    #     },
    #     "AccountType": "Savings",
    #     "AccountBalance": float(0),  # Ensure this is a float
    #     "AccountCurrency": "EUR",
    #     "AccountDescription": "Savings account for Frida Kahlo",
    #     "AccountUser": {
    #         "UserName": "fridaklo",
    #         "UserId": ObjectId("65a546ae4a8f64e8f88fb89e")
    #     }
    # }

    # # Create an account
    # account_id = create_account(account_service, account_data)
    # logging.info(f"Account ID: {account_id}")

    # Attempt to close the account
    # Bad one 671ff0081ec726b417352702
    # Good one 674f052649dab970d1b615a9
    account_id = ObjectId("674f052649dab970d1b615a9")
    close_account(account_service, account_id)

    # # Delete the account
    # delete_account(account_service, account_id)

    # # Retrieve accounts for a specific user by ID
    # # gracehop = ObjectId("66fe219d625d93a100528224")
    # user_id = ObjectId("66fe219d625d93a100528224")  # Replace with a valid ObjectId
    # get_accounts_for_user(account_service, user_id)
    # # Retrieve accounts for a specific user by username
    # username = "fridaklo"  # Replace with a valid username
    # get_accounts_for_user(account_service, username)

if __name__ == "__main__":
    main()
