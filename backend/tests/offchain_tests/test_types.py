import json

from offchain import from_json


def test_from_json__optional_union_result__should_parse_dict_successfully():
    payment_info_response = {"status": "success", "cid": "bcb8c002-68be-4b36-8673-9ff412e6b9ca",
                             "result": {"_ObjectType": "GetInfoCommandResponse", "payment_info": {
                                 "receiver": {"address": "tdm1p5n9msrdfwmtre7t79hx0avlwvqqqqqqqqqqqqqq204wzc",
                                              "business_data": {"name": "Test Merchant - 2021-07-06T09:13:54.043Z",
                                                                "legal_name": "Test Merchant LTD",
                                                                "address": {"city": "New York", "country": "US",
                                                                            "line1": "725 5th Ave",
                                                                            "postal_code": "10022", "state": "NY"}}},
                                 "action": {"amount": 1000000, "currency": "XUS", "action": "charge",
                                            "timestamp": 1625562836056},
                                 "reference_id": "2a46c74d-805d-4932-834d-470e55c0330c",
                                 "description": "Get info command response"}}, "_ObjectType": "CommandResponseObject"}
    init_charge_response = {"status": "success", "cid": "65cb74b1-05e4-4c81-92c0-40a234cdab28",
                            "result": {"_ObjectType": "InitChargePaymentResponse"},
                            "_ObjectType": "CommandResponseObject"}
    # payment_info_result = from_json(json.dumps(payment_info_response))
    init_charge_result = from_json(json.dumps(init_charge_response))
    assert payment_info_result == payment_info_response
    assert init_charge_result == init_charge_response
