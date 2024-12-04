from bson import ObjectId
from typing import Union
from database.connection import MongoDBConnection
from datetime import datetime, timezone

import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class AccountsService:
    """This class provides methods to interact with accounts in the database."""

    def __init__(self, connection: MongoDBConnection, db_name: str, accounts_collection_name: str, users_collection_name: str):
        """Initialize the AccountService with the MongoDB connection and collection names.

        Args:
            connection (MongoDBConnection): The MongoDB connection instance.
            db_name (str): The name of the database.
            accounts_collection_name (str): The name of the accounts collection.
            users_collection_name (str): The name of the users collection.

        Returns:
            None
        """
        self.accounts_collection = connection.get_collection(
            db_name, accounts_collection_name)
        self.users_collection = connection.get_collection(
            db_name, users_collection_name)

    def create_account(self, account_number: str, account_balance: float, account_type: str, user_name: str, user_id: str) -> ObjectId:
        """Create an account and return its ID.
        Args:
            user_name (str): The username of the account holder.
            user_id (str): The user ID of the account holder.
            account_number (str): The account number (9 digits).
            account_balance (float): The initial account balance.
            account_type (str): The type of account (Checking or Savings).
        Returns:
            ObjectId: The ID of the created account.
        """
        # Validate and convert user_id to ObjectId
        user_id_obj = ObjectId(user_id)

        # Check if the user exists in the users collection
        user = self.users_collection.find_one(
            {"_id": user_id_obj, "UserName": user_name})
        if not user:
            logging.error(
                f"User with ID {user_id} and username {user_name} not found.")
            raise ValueError("Invalid user ID or username.")

        # In Python, type hints (like float in function signature) are not enforced at runtime.
        # This means that even if you specify account_balance: float, the actual value passed to the function can still be an integer if it's not explicitly converted to a float.
        # Ensure account_balance is a float
        account_balance = float(account_balance)

        # Construct the account data with default values
        account_data = {
            "_id": ObjectId(),  # Generate a new unique ObjectId
            "AccountNumber": account_number,
            "AccountBank": "LeafyBank",
            "AccountStatus": "Active",
            "AccountIdentificationType": "AccountNumber",
            "AccountDate": {
                "OpeningDate": datetime.now(timezone.utc)
            },
            "AccountType": account_type,
            "AccountBalance": account_balance,
            "AccountCurrency": "EUR",  # Default currency
            "AccountDescription": f"{account_type} account for {user_name}",
            "AccountUser": {
                "UserName": user_name,
                "UserId": user_id_obj
            }
        }
        # Insert the account data into the accounts collection
        result = self.accounts_collection.insert_one(account_data)
        account_id = result.inserted_id
        # Update the user's LinkedAccounts array in the users collection
        self.users_collection.update_one(
            {"_id": user_id_obj},
            {"$addToSet": {"LinkedAccounts": account_id}}
        )
        return account_id

    def delete_account(self, account_id: str) -> bool:
        """Delete an account by its ID.

        Args:
            account_id (str): The ID of the account to delete.

        Returns:
            bool: True if the account was successfully deleted, False otherwise.
        """
        # Delete the account by its ObjectId
        result = self.accounts_collection.delete_one(
            {"_id": ObjectId(account_id)})
        if result.deleted_count > 0:
            # Remove the account ID from all users' LinkedAccounts arrays
            self.users_collection.update_many(
                {"LinkedAccounts": ObjectId(account_id)},
                {"$pull": {"LinkedAccounts": ObjectId(account_id)}}
            )
            return True
        return False

    def get_accounts_for_user(self, user_identifier: Union[str, ObjectId]) -> list[dict]:
        """Retrieve accounts for a specific user.
        Args:
            user_identifier (Union[str, ObjectId]): The user identifier (username or ObjectId of the user).

        Returns:
            list[dict]: A list of accounts associated with the user.
        """
        # Determine if the identifier is an ObjectId or a username
        if isinstance(user_identifier, ObjectId):
            query = {"AccountUser.UserId": user_identifier}
        else:
            query = {"AccountUser.UserName": user_identifier}

        # Retrieve the accounts matching the query
        accounts = list(self.accounts_collection.find(query))
        return accounts

    def get_active_accounts_for_user(self, user_identifier: Union[str, ObjectId]) -> list[dict]:
        """Retrieve active accounts for a specific user.
        Args:
            user_identifier (Union[str, ObjectId]): The user identifier (username or ObjectId of the user).
        Returns:
            list[dict]: A list of active accounts associated with the user.
        """
        # Determine if the identifier is an ObjectId or a username
        # Query for Active accounts only
        if isinstance(user_identifier, ObjectId):
            query = {"AccountUser.UserId": user_identifier,
                     "AccountStatus": "Active"}
        else:
            query = {"AccountUser.UserName": user_identifier,
                     "AccountStatus": "Active"}
        accounts = list(self.accounts_collection.find(query))
        return accounts

    def close_account(self, account_id: str) -> bool:
        """Attempt to close an account by its ID if the balance is zero.
        Args:
            account_id (str): The ID of the account to close.
        Returns:
            bool: True if the account was successfully closed, False otherwise.
        """
        # Convert account_id to ObjectId
        account_oid = ObjectId(account_id)
        # Find the account by its ObjectId
        account = self.accounts_collection.find_one({"_id": account_oid})
        if not account:
            logging.error(f"Account with ID {account_id} not found.")
            return False
        if account.get("AccountBalance", 0) != 0:
            logging.error(
                f"Account with ID {account_id} cannot be closed because it has a remaining balance.")
            return False
        # Update the account status to "Closed" and set the ClosingDate
        result = self.accounts_collection.update_one(
            {"_id": account_oid},
            {
                "$set": {
                    "AccountStatus": "Closed",
                    "AccountDate.ClosingDate": datetime.now(timezone.utc)
                }
            }
        )
        if result.modified_count > 0:
            logging.info(f"Account with ID {account_id} successfully closed.")
            return True
        else:
            logging.error(
                f"Failed to close the account with ID {account_id} due to an unexpected error.")
            return False
