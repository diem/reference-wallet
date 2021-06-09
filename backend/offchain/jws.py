# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import base64, typing
import json

from . import CommandRequestObject, CommandResponseObject, to_json, from_json


def base64url_encode(json):
    return base64.urlsafe_b64encode(json).rstrip(b"=")


PROTECTED_HEADER: bytes = base64url_encode(b'{"alg":"EdDSA"}')
ENCODING: str = "UTF-8"

T = typing.TypeVar("T")


def serialize(
    obj: typing.Union[CommandRequestObject, CommandResponseObject],
    sign: typing.Callable[[bytes], bytes],
) -> bytes:
    return serialize_string(to_json(obj), sign)


def deserialize(
    msg: bytes,
    klass: typing.Type[T],
    verify: typing.Callable[[bytes, bytes], None],
) -> T:
    decoded_body, sig, signing_msg = deserialize_string(msg)

    verify(sig, signing_msg)
    return from_json(decoded_body, klass)


def serialize_string(string: str, sign: typing.Callable[[bytes], bytes]) -> bytes:
    payload = base64url_encode(string.encode(ENCODING))
    msg = signing_message(payload, PROTECTED_HEADER)
    return b".".join([msg, base64url_encode(sign(msg))])


def deserialize_string(msg: bytes) -> typing.Tuple[str, bytes, bytes]:
    text = msg.decode(ENCODING)
    parts = text.split(".")
    if len(parts) != 3:
        raise ValueError(
            "invalid JWS compact message: %s, expect 3 parts: <header>.<payload>.<signature>"
            % text
        )

    header, body, sig = parts
    if (
        json.loads(decode(header.encode(ENCODING)).decode(ENCODING))["alg"]
        != json.loads(decode(PROTECTED_HEADER).decode(ENCODING))["alg"]
    ):
        raise ValueError(
            f"invalid JWS message header: {header}, header must contain {PROTECTED_HEADER}"
        )

    body_bytes = body.encode(ENCODING)
    return (
        decode(body_bytes).decode(ENCODING),
        decode(sig.encode(ENCODING)),
        signing_message(body_bytes, header.encode(ENCODING)),
    )


def signing_message(payload: bytes, header: bytes) -> bytes:
    return b".".join([header, payload])


def decode(msg: bytes) -> bytes:
    return base64.urlsafe_b64decode(fix_padding(msg))


def fix_padding(input: bytes) -> bytes:
    return input + b"=" * (4 - (len(input) % 4))
