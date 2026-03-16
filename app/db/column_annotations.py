import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import func, String, DateTime
from sqlalchemy.orm import mapped_column

uuid_pk = Annotated[
    uuid.UUID,
    mapped_column(primary_key=True, default=uuid.uuid4),
]
created_at = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now()),
]
updated_at = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
]
aware_datetime = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True)),
]
bool_default_false = Annotated[bool, mapped_column(default=False)]
str_not_nullable = Annotated[str, mapped_column(String(255), nullable=False)]
