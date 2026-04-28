from database.connection import MongoDBConnection
from services.accounts_service import AccountsService
from services.users_service import UsersService
from services.bian_service import BianService
from encoder.json_encoder import MyJSONEncoder
from bian.api_catalog import API_CATALOG

import logging

from typing import List, Dict

import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api_models import (
    AccountActivityRequestRequest,
    AccountBalanceRetrieveRequest,
    AccountControlRequest,
    AccountInitiateRequest,
    AccountRequestRequest,
    AccountRetrieveRequest,
    CustomerKYCRetrieveRequest,
    PartyReferenceRequestRequest,
    PartyReferenceRetrieveRequest,
)
from database.connection import MongoDBConnection
from encoder.json_encoder import MyJSONEncoder
from services.accounts_service import AccountsService
from services.customers_service import CustomersService
from shared import registry

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("LEAFYBANK_DB_NAME", "leafy_bank_bian")

app = FastAPI(
    title="Leafy Bank — Accounts (BIAN PartyReferenceDataDirectoryEntry + CurrentAccountFulfillmentArrangement)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Initialize the MongoDB connection
db_name = os.getenv("LEAFYBANK_DB_NAME", "leafy_bank_bian")
accounts_collection_name = "accounts"
users_collection_name = "users"
bian_mapping_collection_name = "bian_mapping"
logging.info(f"Using MongoDB database: {db_name}")
connection = MongoDBConnection(MONGODB_URI)
accounts_service = AccountsService(connection, DB_NAME)
customers_service = CustomersService(connection, DB_NAME)


def _bian_response(envelope: dict) -> Response:
    return Response(
        content=json.dumps(envelope, cls=MyJSONEncoder),
        media_type="application/json",
    )


# Initialize the BianService (read-only access to bian_mapping metadata)
bian_service = BianService(
    connection, db_name, bian_mapping_collection_name)

# ---------- Health / root ----------

@app.get("/")
async def read_root():
    return {
        "service": "leafy-bank-accounts",
        "bian": [
            "PartyReferenceDataDirectoryEntry",
            "CurrentAccountFulfillmentArrangement",
        ],
        "bianVersion": registry.bian_version,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- PartyReferenceDataDirectoryEntry ----------

@app.post("/PartyReferenceDataDirectoryEntry/Retrieve")
async def party_retrieve(body: PartyReferenceRetrieveRequest):
    """BIAN PartyReferenceDataDirectoryEntry / Retrieve."""
    try:
        customer = customers_service.get_customer(body.CustomerReference)
        if not customer:
            raise HTTPException(status_code=404, detail="CustomerReference not found.")
        return _bian_response({
            "CustomerReference": customer["customerId"],
            "PartyReferenceDataDirectoryEntryRecord": registry.to_bian("customers", customer),
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("PartyReferenceDataDirectoryEntry/Retrieve failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal retrieve error.")


@app.post("/PartyReferenceDataDirectoryEntry/Request")
async def party_request(body: PartyReferenceRequestRequest):
    """BIAN PartyReferenceDataDirectoryEntry / Request — list/query customers."""
    try:
        alias_filters = registry.to_alias("customers", body.model_dump(exclude_none=True))
        customers = customers_service.list_customers(alias_filters)
        return _bian_response({
            "PartyReferenceDataDirectoryEntryRecord": [
                registry.to_bian("customers", c) for c in customers
            ],
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("PartyReferenceDataDirectoryEntry/Request failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal list error.")


@app.post("/PartyReferenceDataDirectoryEntry/CustomerKYCRecord/Retrieve")
async def party_kyc_retrieve(body: CustomerKYCRetrieveRequest):
    """BIAN PartyReferenceDataDirectoryEntry / CustomerKYCRecord / Retrieve."""
    try:
        kyc_doc = customers_service.get_customer_kyc(body.CustomerReference)
        if not kyc_doc:
            raise HTTPException(status_code=404, detail="CustomerReference not found.")
        bian_kyc = registry.to_bian(
            "customers", {"kyc": kyc_doc.get("kyc", {})}
        ).get("CustomerKYCRecord", {})
        return _bian_response({
            "CustomerReference": kyc_doc["customerId"],
            "CustomerKYCRecord": bian_kyc,
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("PartyReferenceDataDirectoryEntry/CustomerKYCRecord/Retrieve failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal KYC retrieve error.")


# ---------- CurrentAccountFulfillmentArrangement ----------

@app.post("/CurrentAccountFulfillmentArrangement/Initiate")
async def account_initiate(body: AccountInitiateRequest):
    """BIAN CurrentAccountFulfillmentArrangement / Initiate — open a new account."""
    try:
        alias_body = registry.to_alias("accounts", body.model_dump(exclude_none=True))
        account_doc = accounts_service.create_account(
            customer_ref=alias_body["customerId"],
            product_ref=body.ProductReference,
            account_number=alias_body["accountNumber"],
            currency=alias_body["currency"],
            account_type=alias_body["type"],
            initial_deposit=body.InitialDepositAmount,
        )
        return _bian_response({
            "CurrentAccountReference": account_doc["accountId"],
            "CurrentAccountFulfillmentArrangementRecord": registry.to_bian("accounts", account_doc),
        })
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error("CurrentAccountFulfillmentArrangement/Initiate failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal initiate error.")


@app.post("/CurrentAccountFulfillmentArrangement/Retrieve")
async def account_retrieve(body: AccountRetrieveRequest):
    """BIAN CurrentAccountFulfillmentArrangement / Retrieve.

    Body accepts either `CurrentAccountReference` (preferred) or `CurrentAccountNumber`.
    """
    try:
        if body.CurrentAccountReference:
            account = accounts_service.get_account(body.CurrentAccountReference)
        else:
            account = accounts_service.get_account_by_number(body.CurrentAccountNumber)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found.")
        return _bian_response({
            "CurrentAccountReference": account["accountId"],
            "CurrentAccountFulfillmentArrangementRecord": registry.to_bian("accounts", account),
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("CurrentAccountFulfillmentArrangement/Retrieve failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal retrieve error.")


@app.post("/CurrentAccountFulfillmentArrangement/Request")
async def account_request(body: AccountRequestRequest):
    """BIAN CurrentAccountFulfillmentArrangement / Request — list/query accounts."""
    try:
        alias_filters = registry.to_alias("accounts", body.model_dump(exclude_none=True))
        accounts = accounts_service.list_accounts(alias_filters)
        return _bian_response({
            "CurrentAccountFulfillmentArrangementRecord": [
                registry.to_bian("accounts", a) for a in accounts
            ],
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("CurrentAccountFulfillmentArrangement/Request failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal list error.")


@app.post("/CurrentAccountFulfillmentArrangement/Control")
async def account_control(body: AccountControlRequest):
    """BIAN CurrentAccountFulfillmentArrangement / Control — Close in Phase 1."""
    try:
        account = accounts_service.control_close(
            body.CurrentAccountReference, body.ControlActionReason
        )
        return _bian_response({
            "CurrentAccountReference": account["accountId"],
            "ControlActionType": "Close",
            "CurrentAccountFulfillmentArrangementRecord": registry.to_bian("accounts", account),
        })
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error("CurrentAccountFulfillmentArrangement/Control failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal control error.")


@app.post("/CurrentAccountFulfillmentArrangement/CurrentAccountBalanceRecord/Retrieve")
async def account_balance_retrieve(body: AccountBalanceRetrieveRequest):
    """BIAN CurrentAccountFulfillmentArrangement / CurrentAccountBalanceRecord / Retrieve."""
    try:
        doc = accounts_service.get_balance(body.CurrentAccountReference)
        if not doc:
            raise HTTPException(status_code=404, detail="Account not found.")
        bian = registry.to_bian(
            "accounts", {"balance": doc.get("balance", {}), "currency": doc.get("currency")}
        )
        return _bian_response({
            "CurrentAccountReference": doc["accountId"],
            "CurrentAccountBalanceRecord": bian.get("CurrentAccountBalanceRecord", {}),
            "CurrentAccountCurrencyCode": bian.get("CurrentAccountCurrencyCode"),
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            "CurrentAccountFulfillmentArrangement/CurrentAccountBalanceRecord/Retrieve failed: %s",
            e,
        )
        raise HTTPException(status_code=500, detail="Internal balance retrieve error.")


@app.post("/CurrentAccountFulfillmentArrangement/CurrentAccountTransaction/Request")
async def account_activity_request(body: AccountActivityRequestRequest):
    """BIAN CurrentAccountFulfillmentArrangement / CurrentAccountTransaction / Request.

    Returns ledger legs scoped to either a single account (`CurrentAccountReference`) or
    fanned out across all of a customer's accounts (`CustomerReference`). Exactly one is
    required; cross-field validation in `AccountActivityRequestRequest`.

    The customer fan-out path was added in Phase 5 to power the UI's global recent-activity
    feed in one network call (per umbrella plan-ui-bian-flip § 4.3 / PR-accounts-4).
    """
    try:
        legs = accounts_service.get_recent_activity(
            account_ref=body.CurrentAccountReference,
            customer_ref=body.CustomerReference,
            limit=body.Limit,
        )
        envelope = {
            "CurrentAccountPaymentTransactionRecord": [
                registry.to_bian("transactions", leg) for leg in legs
            ],
        }
        if body.CurrentAccountReference:
            envelope["CurrentAccountReference"] = body.CurrentAccountReference
        else:
            envelope["CustomerReference"] = body.CustomerReference
        return _bian_response(envelope)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# BIAN explorer endpoints (read-only metadata for the UI BIAN modal)
# ---------------------------------------------------------------------------


@app.get("/fetch-bian-mapping")
async def fetch_bian_mapping():
    """Retrieve the singleton bian_mapping document.

    The document maps Mongo camelCase field paths to their BIAN v14 canonical
    names, grouped by domain (customers, accounts, payments, transactions),
    plus a $meta block with version and source info.

    Returns:
        dict: { "mapping": { "$meta": {...}, "customers": {...}, ... } }
    """
    try:
        document = bian_service.get_mapping()
        if document is None:
            raise HTTPException(
                status_code=404, detail="BIAN mapping document not found")
        logging.info("Returning BIAN mapping document")
        return Response(
            content=json.dumps({"mapping": document}, cls=MyJSONEncoder),
            media_type="application/json")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrieving BIAN mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fetch-bian-api-catalog")
async def fetch_bian_api_catalog():
    """Retrieve the BIAN API catalog.

    The catalog describes each backend operation in BIAN v14 terms
    (PascalCase operation names) with placeholder request/response examples.
    Single source of truth: backend/bian/api_catalog.py.

    Returns:
        dict: { "catalog": { "version", "description", "domains": [...] } }
    """
    try:
        logging.info("Returning BIAN API catalog")
        return Response(
            content=json.dumps({"catalog": API_CATALOG}, cls=MyJSONEncoder),
            media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving BIAN API catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        logging.error(
            "CurrentAccountFulfillmentArrangement/CurrentAccountTransaction/Request failed: %s", e
        )
        raise HTTPException(status_code=500, detail="Internal activity error.")
