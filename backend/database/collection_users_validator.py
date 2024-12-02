import logging
from connection import MongoDBConnection
from pymongo.errors import CollectionInvalid

import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_users_collection_with_validation(connection: MongoDBConnection, db_name: str):
    db = connection.get_database(db_name)
    # Create a collection with validation: https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema/#specify-json-schema-validation
    # The validation rules are defined in the JSON schema format
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "User Object Validation",
            "required": ["UserName", "UserEmail", "UserIdentification", "Name", "ResidentialStatus", "CivilStatus", "BirthDate", "Nationality", "JobTitle", "UserAddress"],
            "properties": {
                "UserName": {
                    "bsonType": "string",
                    "description": "'UserName' must be a string and is required"
                },
                "UserEmail": {
                    "bsonType": "string",
                    "pattern": "^.+@.+\..+$",
                    "description": "'UserEmail' must be a valid email address and is required"
                },
                "UserIdentification": {
                    "bsonType": "string",
                    "description": "'UserIdentification' must be a string and is required"
                },
                "Name": {
                    "bsonType": "object",
                    "required": ["FirstName", "LastName", "NamePrefix"],
                    "properties": {
                        "FirstName": {
                            "bsonType": "string",
                            "description": "'FirstName' must be a string and is required"
                        },
                        "LastName": {
                            "bsonType": "string",
                            "description": "'LastName' must be a string and is required"
                        },
                        "NamePrefix": {
                            "bsonType": "string",
                            "description": "'NamePrefix' must be a string and is required"
                        }
                    }
                },
                "ResidentialStatus": {
                    "bsonType": "string",
                    "description": "'ResidentialStatus' must be a string and is required"
                },
                "CivilStatus": {
                    "bsonType": "string",
                    "description": "'CivilStatus' must be a string and is required"
                },
                "BirthDate": {
                    "bsonType": "date",
                    "description": "'BirthDate' must be a date and is required"
                },
                "Nationality": {
                    "bsonType": "string",
                    "description": "'Nationality' must be a string and is required"
                },
                "JobTitle": {
                    "bsonType": "string",
                    "description": "'JobTitle' must be a string and is required"
                },
                "UserAddress": {
                    "bsonType": "object",
                    "required": ["StreetAndNumber", "PostalCode", "City", "Country", "State"],
                    "properties": {
                        "StreetAndNumber": {
                            "bsonType": "string",
                            "description": "'StreetAndNumber' must be a string and is required"
                        },
                        "PostalCode": {
                            "bsonType": "string",
                            "description": "'PostalCode' must be a string and is required"
                        },
                        "City": {
                            "bsonType": "string",
                            "description": "'City' must be a string and is required"
                        },
                        "Country": {
                            "bsonType": "string",
                            "description": "'Country' must be a string and is required"
                        },
                        "State": {
                            "bsonType": "string",
                            "description": "'State' must be a string and is required"
                        }
                    }
                },
                "LinkedAccounts": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "objectId",
                        "description": "'LinkedAccounts' must be an array of ObjectIds"
                    },
                    "description": "'LinkedAccounts' must be an array of ObjectIds"
                },
                "RecentTransactions": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "description": "'RecentTransactions' must be an array of objects"
                    },
                    "description": "'RecentTransactions' must be an array of objects"
                }
            }
        }
    }

    try:
        db.create_collection("users", validator=validator)
        logging.info("Collection created with validation.")
    except CollectionInvalid:
        logging.error("Collection already exists.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    uri = MONGODB_URI
    connection = MongoDBConnection(uri)
    create_users_collection_with_validation(connection, "leafy_bank")
