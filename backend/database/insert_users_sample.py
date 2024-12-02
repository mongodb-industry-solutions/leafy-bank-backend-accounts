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

def insert_users(connection: MongoDBConnection, db_name: str):
    # Get the users collection
    users_collection = connection.get_collection(db_name, "users")

    # Example documents
    documents = [
        {
            "_id": ObjectId("65a546ae4a8f64e8f88fb89e"),
            "UserName": "fridaklo",
            "UserEmail": "frida.klo@gmail.com",
            "UserIdentification": "IDPERSONA01",
            "Name": {
                "FirstName": "Frida",
                "LastName": "Kahlo",
                "NamePrefix": "Miss"
            },
            "ResidentialStatus": "Resident",
            "CivilStatus": "Widow",
            "BirthDate": datetime(1907, 7, 6),
            "Nationality": "Mexican",
            "JobTitle": "Painter",
            "UserAddress": {
                "StreetAndNumber": "Calle de Londres 247",
                "PostalCode": "62240",
                "City": "Mexico City",
                "Country": "Mexico",
                "State": "Mexico City"
            },
            "LinkedAccounts": [
                ObjectId("674dc33d4473ad1e1d4e02d0"),
                ObjectId("674dc33d4473ad1e1d4e02d1"),
                ObjectId("674dc33d4473ad1e1d4e02d2")
            ],
            "RecentTransactions": []
        },
        {
            "_id": ObjectId("66fe219d625d93a100528224"),
            "UserName": "gracehop",
            "UserEmail": "grace.hopper@gmail.com",
            "UserIdentification": "IDPERSONA02",
            "Name": {
                "FirstName": "Grace",
                "LastName": "Hopper",
                "NamePrefix": "Madam"
            },
            "ResidentialStatus": "PermanentResident",
            "CivilStatus": "LegallyDivorced",
            "BirthDate": datetime(1906, 12, 9),
            "Nationality": "American",
            "JobTitle": "Computer Scientist",
            "UserAddress": {
                "StreetAndNumber": "226 W 108th St",
                "PostalCode": "NY 10025",
                "Country": "USA",
                "State": "New York",
                "City": "New York City"
            },
            "LinkedAccounts": [],
            "RecentTransactions": []
        },
        {
            "_id": ObjectId("671ff0081ec726b417352702"),
            "UserName": "adalove",
            "UserEmail": "ada.lovelace@gmail.com",
            "UserIdentification": "IDPERSONA03",
            "Name": {
                "FirstName": "Ada",
                "LastName": "Lovelace",
                "NamePrefix": "Miss"
            },
            "ResidentialStatus": "NonResident",
            "CivilStatus": "Single",
            "BirthDate": datetime(1815, 12, 10),
            "Nationality": "British",
            "JobTitle": "Mathematician",
            "UserAddress": {
                "StreetAndNumber": "3 St James's Square",
                "PostalCode": "SW1Y 4JU",
                "Country": "UK",
                "State": "England",
                "City": "London"
            },
            "LinkedAccounts": [],
            "RecentTransactions": []
        },
        {
            "_id": ObjectId("671ff2451ec726b417352703"),
            "UserName": "claumon",
            "UserEmail": "claude.monet@gmail.com",
            "UserIdentification": "IDPERSONA04",
            "Name": {
                "FirstName": "Claude",
                "LastName": "Monet",
                "NamePrefix": "Mister"
            },
            "ResidentialStatus": "Resident",
            "CivilStatus": "Married",
            "BirthDate": datetime(1840, 11, 14),
            "Nationality": "French",
            "JobTitle": "Painter",
            "UserAddress": {
                "StreetAndNumber": "45 Rue Laffitte",
                "PostalCode": "75009",
                "Country": "France",
                "State": "Île-de-France",
                "City": "Paris"
            },
            "LinkedAccounts": [],
            "RecentTransactions": []
        }
    ]

    # Insert documents
    try:
        users_collection.insert_many(documents)
        logging.info("Documents inserted successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    uri = MONGODB_URI
    connection = MongoDBConnection(uri)
    insert_users(connection, "leafy_bank")
