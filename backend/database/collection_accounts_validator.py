import logging
from connection import MongoDBConnection
from pymongo.errors import CollectionInvalid

import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def remove_validator_from_accounts_collection(connection: MongoDBConnection, db_name: str):
    db = connection.get_database(db_name)
    try:
        # Use the collMod command to remove the validator
        db.command({
            "collMod": "accounts",
            "validator": {},  # Set validator to an empty object to remove it
            "validationLevel": "off"  # Optionally, turn off validation
        })
        logging.info("Validator removed from the accounts collection.")
    except Exception as e:
        logging.error(f"An error occurred while removing the validator: {e}")

def create_accounts_collection_with_validation(connection: MongoDBConnection, db_name: str):
    db = connection.get_database(db_name)
    # Create a collection with validation: https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema/#specify-json-schema-validation
    # The validation rules are defined in the JSON schema format
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "Account Object Validation",
            "required": ["AccountNumber", "AccountBank", "AccountStatus", "AccountDate", "AccountType", "AccountBalance", "AccountCurrency", "AccountUser"],
            "properties": {
                "AccountNumber": {
                    "bsonType": "string",
                    "description": "'AccountNumber' must be a string and is required"
                },
                "AccountBank": {
                    "bsonType": "string",
                    "description": "'AccountBank' must be a string and is required"
                },
                "AccountStatus": {
                    "bsonType": "string",
                    "enum": ["Active", "Closed"],
                    "description": "'AccountStatus' must be either 'Active' or 'Closed' and is required"
                },
                "AccountIdentificationType": {
                    "bsonType": "string",
                    "description": "'AccountIdentificationType' must be a string"
                },
                "AccountDate": {
                    "bsonType": "object",
                    "required": ["OpeningDate"],
                    "properties": {
                        "OpeningDate": {
                            "bsonType": "date",
                            "description": "'OpeningDate' must be a date and is required"
                        },
                        "ClosingDate": {
                            "bsonType": "date",
                            "description": "'ClosingDate' must be a date if the field exists"
                        }
                    }
                },
                "AccountType": {
                    "bsonType": "string",
                    "enum": ["Checking", "Savings"],
                    "description": "'AccountType' must be either 'Checking' or 'Savings' and is required"
                },
                "AccountBalance": {
                    "bsonType": "double",
                    "description": "'AccountBalance' must be a double and is required"
                },
                "AccountCurrency": {
                    "bsonType": "string",
                    "description": "'AccountCurrency' must be a string and is required"
                },
                "AccountDescription": {
                    "bsonType": "string",
                    "description": "'AccountDescription' must be a string"
                },
                "AccountUser": {
                    "bsonType": "object",
                    "required": ["UserName", "UserId"],
                    "properties": {
                        "UserName": {
                            "bsonType": "string",
                            "description": "'UserName' must be a string and is required"
                        },
                        "UserId": {
                            "bsonType": "objectId",
                            "description": "'UserId' must be an ObjectId and is required"
                        }
                    }
                }
            }
        }
    }

    try:
        db.create_collection("accounts", validator=validator)
        logging.info("Collection created with validation.")
    except CollectionInvalid:
        logging.error("Collection already exists.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    uri = MONGODB_URI
    connection = MongoDBConnection(uri)
    create_accounts_collection_with_validation(connection, "leafy_bank")
