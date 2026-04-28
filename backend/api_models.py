"""Pydantic request models for the BIAN PartyReferenceDataDirectoryEntry +
CurrentAccountFulfillmentArrangement service domains.

Field names are BIAN canonical (PascalCase). The runtime registry handles translation
to camelCase Mongo storage keys — these models exist purely for boundary validation,
IDE autocomplete, and OpenAPI request schemas.

Drift between these models and `bian-alias-map.json` is a real risk. Verify periodically.
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
    CustomerReference: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


class PartyReferenceRequestRequest(BaseModel):
    PartyApexStatus: Optional[PartyApexStatusType] = None
    CustomerSegmentType: Optional[str] = None
    PartyType: Optional[PartyTypeEnum] = None
    model_config = ConfigDict(extra="forbid")


class CustomerKYCRetrieveRequest(BaseModel):
    CustomerReference: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


# ---------- CurrentAccountFulfillmentArrangement ----------

class AccountInitiateRequest(BaseModel):
    CustomerReference: str = Field(min_length=1)
    ProductReference: Optional[str] = None
    CurrentAccountType: CurrentAccountTypeEnum
    CurrentAccountNumber: str = Field(min_length=1)
    CurrentAccountCurrencyCode: str = Field(min_length=3, max_length=3)
    InitialDepositAmount: float = Field(ge=0)
    model_config = ConfigDict(extra="forbid")


class AccountRetrieveRequest(BaseModel):
    CurrentAccountReference: Optional[str] = None
    CurrentAccountNumber: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _at_least_one(self):
        if not self.CurrentAccountReference and not self.CurrentAccountNumber:
            raise ValueError(
                "One of CurrentAccountReference or CurrentAccountNumber is required."
            )
        return self


class AccountRequestRequest(BaseModel):
    CustomerReference: Optional[str] = None
    CurrentAccountApexStatus: Optional[CurrentAccountApexStatusType] = None
    CurrentAccountType: Optional[CurrentAccountTypeEnum] = None
    model_config = ConfigDict(extra="forbid")


class AccountControlRequest(BaseModel):
    CurrentAccountReference: str = Field(min_length=1)
    ControlActionType: Literal["Close"]
    ControlActionReason: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class AccountBalanceRetrieveRequest(BaseModel):
    CurrentAccountReference: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


class AccountActivityRequestRequest(BaseModel):
    CurrentAccountReference: str = Field(min_length=1)
    Limit: int = Field(default=20, ge=1, le=100)
    model_config = ConfigDict(extra="forbid")
