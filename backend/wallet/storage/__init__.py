# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from ..config import DB_URL

connect_args = {}

if DB_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DB_URL, connect_args=connect_args)
# engine.echo = True
metadata = MetaData()
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base(metadata=metadata)
Base.query = db_session.query_property()

from .user import *
from .account import *
from .order import *
from .token import *
from .transaction import *
from .logs import *
