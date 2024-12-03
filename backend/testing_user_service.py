from bson import ObjectId
from database.connection import MongoDBConnection
from services.user_service import UserService

import logging
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Initialize the MongoDB connection
    uri = MONGODB_URI
    db_name = "leafy_bank"
    users_collection_name = "users"
    connection = MongoDBConnection(uri)

    # Initialize the UserService
    user_service = UserService(connection, db_name, users_collection_name)

    logging.info("Retrieving users...")
    # Retrieve all users
    users = user_service.get_users()
    logging.info(f"Retrieved {len(users)} users:")
    for user in users:
        print(user)

    logging.info("Retrieving specific users...")
    # Retrieve a specific user by ID
    # claumon = ObjectId("671ff2451ec726b417352703
    user_id = ObjectId("671ff2451ec726b417352703")  # Replace with a valid ObjectId
    logging.info(f"Retrieving user with ID: {user_id}")
    user = user_service.get_user(user_id)
    print(user)

    # Retrieve a specific user by username
    username = "fridaklo"  # Replace with a valid username
    logging.info(f"Retrieving user with username: {username}")
    user = user_service.get_user(username)
    print(user)

if __name__ == "__main__":
    main()
