"""Pydantic request models for the BIAN PartyReferenceDataDirectoryEntry +
CurrentAccountFulfillmentArrangement service domains.

Field names use camelCase alias names (matching Mongo storage). The registry
handles BIAN documentation mapping; no wire translation is done at request time.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

PartyApexStatusType = Literal["PROSPECT", "ACTIVE", "DORMANT", "SUSPENDED", "CLOSED"]
PartyTypeEnum = Literal[
    "INDIVIDUAL", "CORPORATE", "SME", "TRUST", "GOVERNMENT", "FINANCIAL_INSTITUTION"
]
CurrentAccountApexStatusType = Literal[
    "PENDING_ACTIVATION", "ACTIVE", "DORMANT", "FROZEN", "CLOSED", "CHARGED_OFF"
]
CurrentAccountTypeEnum = Literal[
    "CURRENT", "SAVINGS", "FIXED_DEPOSIT", "NOSTRO", "VOSTRO", "GL_ACCOUNT"
]


# ---------- PartyReferenceDataDirectoryEntry ----------

class PartyReferenceRetrieveRequest(BaseModel):
    customerId: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


class PartyReferenceRequestRequest(BaseModel):
    status: Optional[PartyApexStatusType] = None
    segment: Optional[str] = None
    type: Optional[PartyTypeEnum] = None
    model_config = ConfigDict(extra="forbid")


class CustomerKYCRetrieveRequest(BaseModel):
    customerId: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


# ---------- CurrentAccountFulfillmentArrangement ----------

class AccountInitiateRequest(BaseModel):
    customerId: str = Field(min_length=1)
    productId: Optional[str] = None
    type: CurrentAccountTypeEnum
    accountNumber: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    initialDeposit: float = Field(ge=0)
    model_config = ConfigDict(extra="forbid")


class AccountRetrieveRequest(BaseModel):
    accountId: Optional[str] = None
    accountNumber: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _at_least_one(self):
        if not self.accountId and not self.accountNumber:
            raise ValueError("One of accountId or accountNumber is required.")
        return self


class AccountRequestRequest(BaseModel):
    customerId: Optional[str] = None
    status: Optional[CurrentAccountApexStatusType] = None
    type: Optional[CurrentAccountTypeEnum] = None
    model_config = ConfigDict(extra="forbid")


class AccountControlRequest(BaseModel):
    accountId: str = Field(min_length=1)
    controlAction: Literal["Close"]
    controlReason: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class AccountBalanceRetrieveRequest(BaseModel):
    accountId: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


class AccountActivityRequestRequest(BaseModel):
    accountId: Optional[str] = None
    customerId: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _exactly_one(self):
        if bool(self.accountId) == bool(self.customerId):
            raise ValueError("Exactly one of accountId or customerId is required.")
        return self
