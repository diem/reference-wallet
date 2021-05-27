from diem import LocalAccount
from offchain import CommandResponseObject, jws, CommandResponseStatus


def test_serialize_deserialize():
    account = LocalAccount.generate()
    response = CommandResponseObject(
        status=CommandResponseStatus.success,
        cid="3185027f05746f5526683a38fdb5de98",
    )
    ret = jws.serialize(response, account.private_key.sign)

    resp = jws.deserialize(
        ret,
        CommandResponseObject,
        account.private_key.public_key().verify,
    )
    assert resp == response
