# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

swagger_template = {
    "swagger": "",
    "openapi": "3.0.0",
    "components": {
        "securitySchemes": {
            "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT",}
        }
    },
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "dob": {"type": "string", "format": "date"},
                "phone_number": {"type": "string"},
                "country": {"type": "string"},
                "state": {"type": "string"},
                "city": {"type": "string"},
                "address_1": {"type": "string"},
                "address_2": {"type": "string"},
                "zip": {"type": "string"},
            },
            "example": {
                "username": "sunmilee",
                "first_name": "Sunmi",
                "last_name": "Lee",
                "dob": "2020-05-07",
                "address": "1 Hacker Way",
            },
        },
        "DiemCurrencies": {"type": "string", "enum": ["Coin1"],},
        "TransactionDirections": {"type": "string", "enum": ["received", "sent"],},
        "Transaction": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "amount": {"type": "integer"},
                "currency": {"$ref": "#/definitions/DiemCurrencies"},
                "direction": {"$ref": "#/definitions/TransactionDirections"},
                "timestamp": {"type": "string", "format": "date-time"},
                "source": {"$ref": "#/definitions/VaspAccountDetails"},
                "destination": {"$ref": "#/definitions/VaspAccountDetails"},
                "blockchain_tx": {"$ref": "#/definitions/BlockchainTransaction"},
            },
        },
        "VaspAccountDetails": {
            "type": "object",
            "properties": {
                "vasp_name": {"type": "string"},
                "user_id": {"type": "string"},
            },
        },
        "BlockchainTransaction": {
            "type": "object",
            "properties": {
                "version": {"type": "integer"},
                "status": {"type": "string"},
                "expirationTime": {"type": "string"},
                "source": {"type": "string"},
                "destination": {"type": "string"},
                "amount": {"type": "integer"},
                "sequenceNumber": {"type": "integer"},
            },
        },
    },
    "security": [{"BearerAuth": []}],
}
