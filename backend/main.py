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
from bian.api_catalog import API_CATALOG
from database.connection import MongoDBConnection
from encoder.json_encoder import MyJSONEncoder
from services.accounts_service import AccountsService
from services.bian_service import BianService
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

connection = MongoDBConnection(MONGODB_URI)
accounts_service = AccountsService(connection, DB_NAME)
customers_service = CustomersService(connection, DB_NAME)
bian_service = BianService(connection, DB_NAME, "bian-mapping")


def _bian_response(envelope: dict) -> Response:
    return Response(
        content=json.dumps(envelope, cls=MyJSONEncoder),
        media_type="application/json",
    )


def _strip(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


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
    try:
        customer = customers_service.get_customer(body.customerId)
        if not customer:
            raise HTTPException(status_code=404, detail="customerId not found.")
        return _bian_response({
            "customerId": customer["customerId"],
            "customer": _strip(customer),
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("PartyReferenceDataDirectoryEntry/Retrieve failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal retrieve error.")


@app.post("/PartyReferenceDataDirectoryEntry/Request")
async def party_request(body: PartyReferenceRequestRequest):
    try:
        customers = customers_service.list_customers(body.model_dump(exclude_none=True))
        return _bian_response({
            "customers": [_strip(c) for c in customers],
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("PartyReferenceDataDirectoryEntry/Request failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal list error.")


@app.post("/PartyReferenceDataDirectoryEntry/CustomerKYCRecord/Retrieve")
async def party_kyc_retrieve(body: CustomerKYCRetrieveRequest):
    try:
        doc = customers_service.get_customer_kyc(body.customerId)
        if not doc:
            raise HTTPException(status_code=404, detail="customerId not found.")
        return _bian_response({
            "customerId": doc["customerId"],
            "kyc": doc.get("kyc", {}),
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("PartyReferenceDataDirectoryEntry/CustomerKYCRecord/Retrieve failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal KYC retrieve error.")


# ---------- CurrentAccountFulfillmentArrangement ----------

@app.post("/CurrentAccountFulfillmentArrangement/Initiate")
async def account_initiate(body: AccountInitiateRequest):
    try:
        account_doc = accounts_service.create_account(
            customer_ref=body.customerId,
            product_ref=body.productId,
            account_number=body.accountNumber,
            currency=body.currency,
            account_type=body.type,
            initial_deposit=body.initialDeposit,
        )
        return _bian_response({
            "accountId": account_doc["accountId"],
            "account": _strip(account_doc),
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
    try:
        if body.accountId:
            account = accounts_service.get_account(body.accountId)
        else:
            account = accounts_service.get_account_by_number(body.accountNumber)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found.")
        return _bian_response({
            "accountId": account["accountId"],
            "account": _strip(account),
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("CurrentAccountFulfillmentArrangement/Retrieve failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal retrieve error.")


@app.post("/CurrentAccountFulfillmentArrangement/Request")
async def account_request(body: AccountRequestRequest):
    try:
        accounts = accounts_service.list_accounts(body.model_dump(exclude_none=True))
        return _bian_response({
            "accounts": [_strip(a) for a in accounts],
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error("CurrentAccountFulfillmentArrangement/Request failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal list error.")


@app.post("/CurrentAccountFulfillmentArrangement/Control")
async def account_control(body: AccountControlRequest):
    try:
        account = accounts_service.control_close(body.accountId, body.controlReason)
        return _bian_response({
            "accountId": account["accountId"],
            "controlAction": body.controlAction,
            "account": _strip(account),
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
    try:
        doc = accounts_service.get_balance(body.accountId)
        if not doc:
            raise HTTPException(status_code=404, detail="Account not found.")
        return _bian_response({
            "accountId": doc["accountId"],
            "balance": doc.get("balance", {}),
            "currency": doc.get("currency"),
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
    try:
        legs = accounts_service.get_recent_activity(
            account_ref=body.accountId,
            customer_ref=body.customerId,
            limit=body.limit,
        )
        envelope = {"transactions": [_strip(leg) for leg in legs]}
        if body.accountId:
            envelope["accountId"] = body.accountId
        else:
            envelope["customerId"] = body.customerId
        return _bian_response(envelope)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            "CurrentAccountFulfillmentArrangement/CurrentAccountTransaction/Request failed: %s", e
        )
        raise HTTPException(status_code=500, detail="Internal activity error.")


# ---------------------------------------------------------------------------
# BIAN explorer endpoints (read-only metadata for the UI BIAN modal)
# ---------------------------------------------------------------------------

@app.get("/fetch-bian-mapping")
async def fetch_bian_mapping():
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
    try:
        logging.info("Returning BIAN API catalog")
        return Response(
            content=json.dumps({"catalog": API_CATALOG}, cls=MyJSONEncoder),
            media_type="application/json")
    except Exception as e:
        logging.error(f"Error retrieving BIAN API catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
