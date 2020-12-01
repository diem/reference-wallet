# pyre-strict

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context
import os
import sys
from typing import Optional

import dramatiq
import redis
from dramatiq.brokers.redis import RedisBroker, Broker
from dramatiq.encoder import PickleEncoder
from dramatiq.results import Results
from dramatiq.results.backends.redis import RedisBackend

import logging

logging.basicConfig(
    format="[%(asctime)s][%(threadName)s][%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
# logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)


REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
DB_URL: str = os.getenv("DB_URL", "sqlite:////tmp/test.db")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin@lrw")
ADMIN_LOGIN_ENABLED: bool = True if os.getenv(
    "ADMIN_LOGIN_ENABLED"
) is not None else False

SECRET_KEY: str = os.getenv("SECRET_KEY", "you-will-never-guess")
SESSION_TYPE: str = "redis"


# init redis and dramatiq broker
def setup_redis_broker() -> None:
    _connection_pool: redis.BlockingConnectionPool = redis.BlockingConnectionPool(
        host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD
    )
    _redis_db: redis.StrictRedis = redis.StrictRedis(connection_pool=_connection_pool)
    _result_backend = RedisBackend(encoder=PickleEncoder(), client=_redis_db)
    _result_middleware = Results(backend=_result_backend)
    broker: Broker = RedisBroker(
        connection_pool=_connection_pool,
        middleware=[_result_middleware],
        namespace="lrw",
    )
    dramatiq.set_broker(broker)
    dramatiq.set_encoder(dramatiq.PickleEncoder())


if dramatiq.broker.global_broker is None:
    if "VASP_ADDR" in os.environ:
        context.set(context.from_env())

    setup_redis_broker()
