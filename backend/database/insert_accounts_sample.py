import logging
from bson import ObjectId
from datetime import datetime
from connection import MongoDBConnection

import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def insert_accounts(connection: MongoDBConnection, db_name: str):
    # Get the accounts collection
    accounts_collection = connection.get_collection(db_name, "accounts")
    # Example documents
    documents = [
        {
            "_id": ObjectId("674dc33d4473ad1e1d4e02d0"),
            "AccountNumber": "1234567890",
            "AccountBank": "LeafyBank",
            "AccountStatus": "Active",
            "AccountIdentificationType": "AccountNumber",
            "AccountDate": {
                "OpeningDate": datetime(2023, 1, 15),
                # Omit ClosingDate if it is None
            },
            "AccountType": "Checking",
            "AccountBalance": float(2500),  # Convert to float
            "AccountCurrency": "EUR",
            "AccountDescription": "Primary checking account",
            "AccountUser": {
                "UserName": "fridaklo",
                "UserId": ObjectId("65a546ae4a8f64e8f88fb89e")
            }
        },
        {
            "_id": ObjectId("674dc33d4473ad1e1d4e02d1"),
            "AccountNumber": "9876543210",
            "AccountBank": "LeafyBank",
            "AccountStatus": "Active",
            "AccountIdentificationType": "AccountNumber",
            "AccountDate": {
                "OpeningDate": datetime(2022, 6, 10),
                # Omit ClosingDate if it is None
            },
            "AccountType": "Savings",
            "AccountBalance": float(5000),  # Convert to float
            "AccountCurrency": "EUR",
            "AccountDescription": "High-interest savings account",
            "AccountUser": {
                "UserName": "fridaklo",
                "UserId": ObjectId("65a546ae4a8f64e8f88fb89e")
            }
        },
        {
            "_id": ObjectId("674dc33d4473ad1e1d4e02d2"),
            "AccountNumber": "1122334455",
            "AccountBank": "LeafyBank",
            "AccountStatus": "Closed",
            "AccountIdentificationType": "AccountNumber",
            "AccountDate": {
                "OpeningDate": datetime(2020, 3, 20),
                "ClosingDate": datetime(2023, 2, 28)  # Ensure this is a date
            },
            "AccountType": "Checking",
            "AccountBalance": float(0),  # Convert to float
            "AccountCurrency": "EUR",
            "AccountDescription": "Old checking account",
            "AccountUser": {
                "UserName": "fridaklo",
                "UserId": ObjectId("65a546ae4a8f64e8f88fb89e")
            }
        }
    ]

    # Insert documents
    try:
        accounts_collection.insert_many(documents)
        logging.info("Documents inserted successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    uri = MONGODB_URI
    connection = MongoDBConnection(uri)
    insert_accounts(connection, "leafy_bank")
