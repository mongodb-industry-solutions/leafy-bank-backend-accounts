from bson import ObjectId
from typing import Dict
from database.connection import MongoDBConnection

class AccountService:
    def __init__(self, connection: MongoDBConnection, db_name: str, accounts_collection_name: str, users_collection_name: str):
        self.accounts_collection = connection.get_collection(db_name, accounts_collection_name)
        self.users_collection = connection.get_collection(db_name, users_collection_name)

    def create_account(self, account_data: Dict) -> ObjectId:
        # Insert the account data into the accounts collection
        result = self.accounts_collection.insert_one(account_data)
        account_id = result.inserted_id

        # Update the user's LinkedAccounts array in the users collection
        user_id = account_data["AccountUser"]["UserId"]
        self.users_collection.update_one(
            {"_id": user_id},
            {"$addToSet": {"LinkedAccounts": account_id}}
        )

        return account_id

    def delete_account(self, account_id: str) -> bool:
        # Delete the account by its ObjectId
        result = self.accounts_collection.delete_one({"_id": ObjectId(account_id)})
        if result.deleted_count > 0:
            # Remove the account ID from all users' LinkedAccounts arrays
            self.users_collection.update_many(
                {"LinkedAccounts": ObjectId(account_id)},
                {"$pull": {"LinkedAccounts": ObjectId(account_id)}}
            )
            return True
        return False
