"""
This module defines the declarative base for all SQLAlchemy models.
"""
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Create a metadata object with a naming convention
# for constraints, which is good practice.
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

# Define the declarative base
Base = declarative_base(metadata=metadata)
