from datetime import timedelta
from uuid import uuid4

from app.core.security import create_token, decode_token, hash_password, verify_password


def test_password_hashing_and_verification() -> None:
    password = "correct horse battery staple"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("wrong password", password_hash)


def test_access_token_round_trip() -> None:
    user_id = uuid4()
    token = create_token(user_id, "access", expires_delta=timedelta(minutes=5))

    assert decode_token(token, "access") == user_id
