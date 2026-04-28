import logging
from typing import Optional

from database.connection import MongoDBConnection

logger = logging.getLogger(__name__)


class CustomersService:
    """Read-side helpers for the BIAN PartyReferenceDataDirectoryEntry service domain.

    Backed by `customers` on `leafy_bank_bian` (v4 nested shape: identification / contact / kyc).
    """

    def __init__(self, connection: MongoDBConnection, db_name: str):
        self.customers = connection.get_database(db_name)["customers"]

    def get_customer(self, customer_ref: str) -> Optional[dict]:
        return self.customers.find_one({"customerId": customer_ref})

    def list_customers(self, filters: dict) -> list[dict]:
        query = {}
        if (status := filters.get("status")):
            query["status"] = status
        if (segment := filters.get("segment")):
            query["segment"] = segment
        if (party_type := filters.get("type")):
            query["type"] = party_type
        return list(self.customers.find(query))

    def get_customer_kyc(self, customer_ref: str) -> Optional[dict]:
        customer = self.customers.find_one(
            {"customerId": customer_ref}, {"customerId": 1, "kyc": 1}
        )
        if not customer:
            return None
        return {"customerId": customer["customerId"], "kyc": customer.get("kyc", {})}
