"""Static catalog describing the backend's API operations in BIAN v14 terms.

This is the single source of truth for the "BIAN API" tab in the frontend
explorer. Each operation carries:
  - id: stable client-side key
  - bianOperationName: PascalCase BIAN canonical operation name
  - method, path: HTTP contract
  - summary: short human description
  - request.example, response.example: placeholder JSON shapes (replace with
    real schemas once finalized)

To update real schemas later, edit only this file -- the frontend renders
whatever this catalog returns without code changes.
"""

API_CATALOG = {
    "version": "v14",
    "description": (
        "Dual-layer naming: BIAN v14 PascalCase names "
        "([Object][Attribute][SemanticType]) used at the API/contract layer, "
        "Mongo camelCase used at the data layer."
    ),
    "domains": [
        {
            "key": "customers",
            "label": "Customers",
            "bianServiceDomain": "Customer Reference Data Directory",
            "operations": [
                {
                    "id": "retrieveCustomerReferenceDataDirectory",
                    "bianOperationName": "RetrieveCustomerReferenceDataDirectory",
                    "method": "GET",
                    "path": "/fetch-customers",
                    "summary": "Retrieve all customers in the directory.",
                    "request": {"example": {}},
                    "response": {
                        "example": {
                            "customers": [
                                {
                                    "CustomerReference": "C-0001",
                                    "PartyLegalName": "Ada Lovelace",
                                    "PartyApexStatus": "Active",
                                    "CustomerSegmentType": "Retail",
                                    "CustomerSinceDate": "2018-04-12"
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "retrieveCustomerReferenceDataRecord",
                    "bianOperationName": "RetrieveCustomerReferenceDataRecord",
                    "method": "GET",
                    "path": "/find-customer",
                    "summary": "Retrieve a single customer by CustomerReference.",
                    "request": {
                        "example": {"customerReference": "C-0001"}
                    },
                    "response": {
                        "example": {
                            "customer": {
                                "CustomerReference": "C-0001",
                                "PartyLegalName": "Ada Lovelace",
                                "PartyApexStatus": "Active",
                                "PartyContactRecord": {
                                    "PartyContactEmailAddress": "ada@example.com",
                                    "PartyContactPhoneNumber": "+1-555-0100"
                                },
                                "CustomerKYCRecord": {
                                    "CustomerKYCProcedureStatus": "Verified",
                                    "CustomerKYCVerificationLevelType": "Enhanced"
                                }
                            }
                        }
                    }
                },
                {
                    "id": "registerCustomerReferenceDataRecord",
                    "bianOperationName": "RegisterCustomerReferenceDataRecord",
                    "method": "POST",
                    "path": "/create-customer",
                    "summary": "Register a new customer reference data record.",
                    "request": {
                        "example": {
                            "PartyLegalName": "Grace Hopper",
                            "PartyDateOfBirthDate": "1906-12-09",
                            "CustomerSegmentType": "Retail",
                            "PartyContactEmailAddress": "grace@example.com"
                        }
                    },
                    "response": {
                        "example": {
                            "message": "Customer registered successfully",
                            "CustomerReference": "C-0042"
                        }
                    }
                }
            ]
        },
        {
            "key": "accounts",
            "label": "Accounts",
            "bianServiceDomain": "Current Account Fulfillment",
            "operations": [
                {
                    "id": "retrieveCurrentAccountDirectory",
                    "bianOperationName": "RetrieveCurrentAccountDirectory",
                    "method": "POST",
                    "path": "/fetch-accounts",
                    "summary": "Retrieve all current accounts.",
                    "request": {"example": {}},
                    "response": {
                        "example": {
                            "accounts": [
                                {
                                    "CurrentAccountReference": "A-1001",
                                    "CurrentAccountNumber": "000123456789",
                                    "CurrentAccountType": "Checking",
                                    "CurrentAccountApexStatus": "Active",
                                    "CurrentAccountCurrencyCode": "USD",
                                    "CurrentAccountBalanceAmount": 4250.75
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "retrieveActiveCurrentAccountDirectory",
                    "bianOperationName": "RetrieveActiveCurrentAccountDirectory",
                    "method": "POST",
                    "path": "/fetch-active-accounts",
                    "summary": "Retrieve only currently active current accounts.",
                    "request": {"example": {}},
                    "response": {
                        "example": {
                            "accounts": [
                                {
                                    "CurrentAccountReference": "A-1001",
                                    "CurrentAccountApexStatus": "Active",
                                    "CurrentAccountBalanceAmount": 4250.75
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "retrieveCurrentAccountByNumber",
                    "bianOperationName": "RetrieveCurrentAccountByNumber",
                    "method": "POST",
                    "path": "/find-account-by-number",
                    "summary": "Retrieve a current account by its account number.",
                    "request": {
                        "example": {"CurrentAccountNumber": "000123456789"}
                    },
                    "response": {
                        "example": {
                            "account": {
                                "CurrentAccountReference": "A-1001",
                                "CurrentAccountNumber": "000123456789",
                                "CurrentAccountApexStatus": "Active",
                                "CurrentAccountBalanceAmount": 4250.75
                            }
                        }
                    }
                },
                {
                    "id": "initiateCurrentAccountFulfillment",
                    "bianOperationName": "InitiateCurrentAccountFulfillment",
                    "method": "POST",
                    "path": "/create-account",
                    "summary": "Open a new current account for a customer.",
                    "request": {
                        "example": {
                            "CustomerReference": "C-0001",
                            "CurrentAccountNumber": "000999888777",
                            "CurrentAccountType": "Checking",
                            "CurrentAccountBalanceAmount": 0.0,
                            "CurrentAccountCurrencyCode": "USD"
                        }
                    },
                    "response": {
                        "example": {
                            "message": "Account opened successfully",
                            "CurrentAccountReference": "A-1042"
                        }
                    }
                },
                {
                    "id": "terminateCurrentAccountFulfillment",
                    "bianOperationName": "TerminateCurrentAccountFulfillment",
                    "method": "POST",
                    "path": "/close-account",
                    "summary": "Close a current account (balance must be zero).",
                    "request": {
                        "example": {"CurrentAccountReference": "A-1001"}
                    },
                    "response": {
                        "example": {
                            "message": "Account closed successfully",
                            "CurrentAccountReference": "A-1001",
                            "CurrentAccountCloseDate": "2026-04-28"
                        }
                    }
                },
                {
                    "id": "retrieveCurrentAccountsForCustomer",
                    "bianOperationName": "RetrieveCurrentAccountsForCustomer",
                    "method": "POST",
                    "path": "/fetch-accounts-for-user",
                    "summary": "Retrieve all current accounts for a given customer.",
                    "request": {
                        "example": {"CustomerReference": "C-0001"}
                    },
                    "response": {
                        "example": {
                            "accounts": [
                                {
                                    "CurrentAccountReference": "A-1001",
                                    "CurrentAccountType": "Checking",
                                    "CurrentAccountBalanceAmount": 4250.75
                                },
                                {
                                    "CurrentAccountReference": "A-1002",
                                    "CurrentAccountType": "Savings",
                                    "CurrentAccountBalanceAmount": 18000.00
                                }
                            ]
                        }
                    }
                }
            ]
        },
        {
            "key": "payments",
            "label": "Payments",
            "bianServiceDomain": "Payment Order",
            "operations": [
                {
                    "id": "retrievePaymentOrderDirectory",
                    "bianOperationName": "RetrievePaymentOrderDirectory",
                    "method": "GET",
                    "path": "/fetch-payments",
                    "summary": "Retrieve the directory of payment orders.",
                    "request": {"example": {}},
                    "response": {
                        "example": {
                            "payments": [
                                {
                                    "PaymentOrderReference": "P-7001",
                                    "PaymentApexStatus": "Settled",
                                    "PaymentRailType": "ACH",
                                    "PaymentInstructedAmount": 1200.00,
                                    "PaymentInstructedCurrencyCode": "USD"
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "initiatePaymentOrder",
                    "bianOperationName": "InitiatePaymentOrder",
                    "method": "POST",
                    "path": "/initiate-payment",
                    "summary": "Initiate a new payment order.",
                    "request": {
                        "example": {
                            "DebtorAccountReference": "A-1001",
                            "CreditorAccountNumber": "000444555666",
                            "CreditorBankIdentifierCode": "BOFAUS3N",
                            "PaymentInstructedAmount": 1200.00,
                            "PaymentInstructedCurrencyCode": "USD",
                            "PaymentRailType": "ACH",
                            "RemittanceUnstructuredInformationText": "Invoice 2026-0042"
                        }
                    },
                    "response": {
                        "example": {
                            "PaymentOrderReference": "P-7042",
                            "PaymentApexStatus": "Received",
                            "PaymentEndToEndIdentifier": "E2E-2026-0042",
                            "PaymentReceivedDateTime": "2026-04-28T17:02:11Z"
                        }
                    }
                },
                {
                    "id": "retrievePaymentOrderRecord",
                    "bianOperationName": "RetrievePaymentOrderRecord",
                    "method": "GET",
                    "path": "/find-payment",
                    "summary": "Retrieve a single payment order by reference.",
                    "request": {
                        "example": {"PaymentOrderReference": "P-7042"}
                    },
                    "response": {
                        "example": {
                            "payment": {
                                "PaymentOrderReference": "P-7042",
                                "PaymentApexStatus": "Settled",
                                "PaymentInstructedAmount": 1200.00,
                                "PaymentSettledDateTime": "2026-04-28T17:08:55Z",
                                "PaymentFraudDecisionType": "Approved"
                            }
                        }
                    }
                }
            ]
        },
        {
            "key": "transactions",
            "label": "Transactions",
            "bianServiceDomain": "Transaction Engine",
            "operations": [
                {
                    "id": "retrieveTransactionDirectory",
                    "bianOperationName": "RetrieveTransactionDirectory",
                    "method": "GET",
                    "path": "/fetch-transactions",
                    "summary": "Retrieve the directory of posted transactions.",
                    "request": {"example": {}},
                    "response": {
                        "example": {
                            "transactions": [
                                {
                                    "TransactionReference": "T-9001",
                                    "CurrentAccountReference": "A-1001",
                                    "TransactionType": "Debit",
                                    "TransactionAmount": 42.50,
                                    "TransactionCurrencyCode": "USD",
                                    "TransactionBookingDate": "2026-04-27"
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "retrieveTransactionsForAccount",
                    "bianOperationName": "RetrieveTransactionsForAccount",
                    "method": "GET",
                    "path": "/fetch-transactions-for-account",
                    "summary": "Retrieve all transactions for a specific account.",
                    "request": {
                        "example": {"CurrentAccountReference": "A-1001"}
                    },
                    "response": {
                        "example": {
                            "transactions": [
                                {
                                    "TransactionReference": "T-9001",
                                    "TransactionType": "Debit",
                                    "TransactionAmount": 42.50,
                                    "CurrentAccountBalanceAfterTransactionAmount": 4208.25,
                                    "TransactionDescriptionText": "Coffee shop"
                                },
                                {
                                    "TransactionReference": "T-9002",
                                    "TransactionType": "Credit",
                                    "TransactionAmount": 2500.00,
                                    "CurrentAccountBalanceAfterTransactionAmount": 6708.25,
                                    "TransactionDescriptionText": "Payroll deposit"
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "retrieveTransactionRecord",
                    "bianOperationName": "RetrieveTransactionRecord",
                    "method": "GET",
                    "path": "/find-transaction",
                    "summary": "Retrieve a single transaction by reference.",
                    "request": {
                        "example": {"TransactionReference": "T-9001"}
                    },
                    "response": {
                        "example": {
                            "transaction": {
                                "TransactionReference": "T-9001",
                                "CurrentAccountReference": "A-1001",
                                "TransactionType": "Debit",
                                "TransactionAmount": 42.50,
                                "TransactionCurrencyCode": "USD",
                                "TransactionBookingDate": "2026-04-27",
                                "TransactionCounterpartyRecord": {
                                    "CounterpartyName": "Blue Bottle Coffee",
                                    "CounterpartyCountryCode": "US"
                                }
                            }
                        }
                    }
                }
            ]
        }
    ]
}
