import uuid


def generate_cid() -> str:
    return str(uuid.uuid4())
