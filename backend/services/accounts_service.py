import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from database.connection import MongoDBConnection
from shared.refs import derive_ref

logger = logging.getLogger(__name__)


class AccountsService:
    """Account lifecycle for the BIAN CurrentAccountFulfillmentArrangement service domain.

    Backed by `accounts` on `leafy_bank_bian` (v4 shape: nested balance/interest/signatories/
    statement/gl). Customer references are string refs (`CUST-...`); account references are
    string refs (`ACC-...`). No ObjectIds in the wire contract.
    """

    DEFAULT_INITIAL_BALANCE_LIMIT = 1_000_000.0

    # v6: gl.accountCode is a numeric FK to glAccounts.accountCode.
    # Customer Deposits — Current → 2100; Customer Deposits — Savings → 2200.
    GL_CODE_BY_TYPE = {
        "CURRENT": "2100",
        "SAVINGS": "2200",
    }

    # v7: accountBank holds the holding institution's display name.
    ACCOUNT_BANK = "Leafy Bank"

    def __init__(self, connection: MongoDBConnection, db_name: str):
        db = connection.get_database(db_name)
        self.accounts = db["accounts"]
        self.customers = db["customers"]
        self.transactions = db["transactions"]

    def get_account(self, account_ref: str) -> Optional[dict]:
        return self.accounts.find_one({"accountId": account_ref})

    def get_account_by_number(self, account_number: str) -> Optional[dict]:
        return self.accounts.find_one({"accountNumber": account_number})

    def list_accounts(self, filters: dict) -> list[dict]:
        query = {}
        if (customer_ref := filters.get("customerId")):
            query["customerSnapshot.customerId"] = customer_ref
        if (status := filters.get("status")):
            query["status"] = status
        if (acct_type := filters.get("type")):
            query["type"] = acct_type
        return list(self.accounts.find(query))

    def get_balance(self, account_ref: str) -> Optional[dict]:
        doc = self.accounts.find_one(
            {"accountId": account_ref}, {"accountId": 1, "balance": 1, "currency": 1}
        )
        return doc

    def get_recent_activity(
        self,
        account_ref: Optional[str] = None,
        customer_ref: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Fetch recent transactions scoped either to one account or to all of a customer's accounts.

        Exactly one of `account_ref` / `customer_ref` must be supplied (handler enforces this
        via Pydantic). Fan-out path resolves the customer's owned accountIds first, then queries
        the transactions collection with `$in`. Sort + limit applied across the merged set.

        v4_21 shape: accountId is nested under payer.accountId / payee.accountId (no top-level
        accountId field), so ownership is matched via $or on both sides.
        """
        if bool(account_ref) == bool(customer_ref):
            raise ValueError(
                "Exactly one of account_ref or customer_ref must be provided."
            )

        if account_ref:
            query = {"$or": [{"payer.accountId": account_ref}, {"payee.accountId": account_ref}]}
        else:
            owned = list(
                self.accounts.find(
                    {"customerSnapshot.customerId": customer_ref}, {"accountId": 1, "_id": 0}
                )
            )
            owned_ids = [a["accountId"] for a in owned]
            if not owned_ids:
                return []
            query = {
                "$or": [
                    {"payer.accountId": {"$in": owned_ids}},
                    {"payee.accountId": {"$in": owned_ids}},
                ]
            }

        cursor = (
            self.transactions.find(query)
            .sort("bookingDate", -1)
            .limit(limit)
        )
        return list(cursor)

    def create_account(
        self,
        customer_ref: str,
        product_ref: Optional[str],
        account_number: str,
        currency: str,
        account_type: str,
        initial_deposit: float,
    ) -> dict:
        if initial_deposit < 0:
            raise ValueError("InitialDepositAmount must be >= 0.")
        if initial_deposit > self.DEFAULT_INITIAL_BALANCE_LIMIT:
            raise ValueError(
                f"InitialDepositAmount exceeds the limit of {self.DEFAULT_INITIAL_BALANCE_LIMIT}."
            )
        if account_type not in ("CURRENT", "SAVINGS", "FIXED_DEPOSIT", "NOSTRO", "VOSTRO", "GL_ACCOUNT"):
            raise ValueError(f"Unsupported CurrentAccountType: {account_type}.")

        customer = self.customers.find_one({"customerId": customer_ref})
        if not customer:
            raise ValueError(f"Customer {customer_ref} not found.")

        if self.accounts.find_one({"accountNumber": account_number}):
            raise ValueError("An account with this number already exists.")

        oid = ObjectId()
        account_id = derive_ref("ACC", oid)
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        ca_code = "CUR" if account_type == "CURRENT" else "SAV"
        product_id = product_ref or f"PROD-STD-{ca_code}-{currency}"
        # v6: top-level customerId removed; customerSnapshot.customerId is the FK.
        # v6 schema only defines DEPOSIT GL codes (2100/2200). Other account types
        # fall back to None — they shouldn't reach this branch in current scope.
        gl_account_code = self.GL_CODE_BY_TYPE.get(account_type)

        doc = {
            "_id": oid,
            "accountId": account_id,
            "accountNumber": account_number,
            "accountBank": self.ACCOUNT_BANK,
            "type": account_type,
            "status": "ACTIVE",
            "customerSnapshot": {"customerId": customer_ref},
            "productId": product_id,
            "branchId": "BRANCH-DEFAULT-001",
            "currency": currency,
            "openedAt": today,
            "closedAt": None,
            "maturesAt": None,
            "linkedCardIds": [],
            "linkedMandateIds": [],
            "balance": {
                "current": initial_deposit,
                "available": initial_deposit,
                "ledger": initial_deposit,
                "hold": 0,
                "overdraftLimit": 0,
                "updatedAt": now,
            },
            "interest": {
                "rate": 0.005 if account_type == "CURRENT" else 0.020,
                "accrualMethod": "ACT_365",
                "accrued": 0,
                "lastAccrualAt": None,
                "nextPaymentAt": None,
                "paymentAccountId": None,
            },
            "signatories": [
                {
                    "customerId": customer_ref,
                    "type": "PRIMARY",
                    "signingRule": "SOLE",
                    "addedAt": today,
                }
            ],
            "restrictions": [],
            "statement": {
                "frequency": "MONTHLY",
                "deliveryChannel": "EMAIL",
                "lastGeneratedAt": None,
                "nextScheduledAt": None,
            },
            "gl": {
                "accountCode": gl_account_code,
                "costCenter": "CC-RETAIL-DEFAULT",
                "profitCenter": "PC-RETAIL-DEFAULT",
            },
            "createdAt": now,
            "updatedAt": now,
            "createdBy": "SERVICE-ACCOUNTS",
            "version": 1,
            "sourceSystem": "leafy-bank-accounts-service",
        }
        self.accounts.insert_one(doc)
        return doc

    def control_close(self, account_ref: str, reason: Optional[str] = None) -> dict:
        account = self.accounts.find_one({"accountId": account_ref})
        if not account:
            raise ValueError(f"Account {account_ref} not found.")
        if account["status"] == "CLOSED":
            raise ValueError("Account is already CLOSED.")
        if (account.get("balance") or {}).get("current", 0) != 0:
            raise ValueError("Account cannot be CLOSED while it carries a non-zero balance.")

        now = datetime.now(timezone.utc)
        update = {
            "$set": {
                "status": "CLOSED",
                "closedAt": now,
                "balance.updatedAt": now,
                "updatedAt": now,
            }
        }
        if reason:
            update["$push"] = {
                "restrictions": {
                    "type": "CLOSURE_REASON",
                    "description": reason,
                    "appliedAt": now,
                }
            }
        return self.accounts.find_one_and_update(
            {"accountId": account_ref}, update, return_document=True
        )
