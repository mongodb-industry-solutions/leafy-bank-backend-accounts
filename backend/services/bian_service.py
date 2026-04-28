from database.connection import MongoDBConnection

import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class BianService:
    """This class provides read-only access to the BIAN mapping metadata document."""

    def __init__(self, connection: MongoDBConnection, db_name: str, bian_mapping_collection_name: str):
        """Initialize the BianService with the MongoDB connection and collection name.

        Args:
            connection (MongoDBConnection): The MongoDB connection instance.
            db_name (str): The name of the database.
            bian_mapping_collection_name (str): The name of the BIAN mapping collection.

        Returns:
            None
        """
        self.bian_mapping_collection = connection.get_collection(
            db_name, bian_mapping_collection_name)

    def get_mapping(self) -> dict:
        """Retrieve the singleton BIAN mapping document.

        The bian_mapping collection contains exactly one document describing
        the Mongo camelCase -> BIAN v14 canonical-name mapping for each domain
        (customers, accounts, payments, transactions) plus a $meta block.

        Returns:
            dict: The mapping document with _id excluded, or None if not found.
        """
        logging.info("Retrieving BIAN mapping document...")
        document = self.bian_mapping_collection.find_one({}, {"_id": 0})
        if document is None:
            logging.error("No BIAN mapping document found in the collection")
        else:
            logging.info("BIAN mapping document found")
        return document
