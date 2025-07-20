import os
import uuid
import logging
from datetime import datetime
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import create_engine, Table, Column, MetaData, String, JSON, DateTime, Boolean, Enum
from sqlalchemy.sql import insert
from src.config.sql_server_config import SQLServerConfig

logger = logging.getLogger(__name__)

class MessageRepository:
    def __init__(self):
        self.engine = create_engine(SQLServerConfig().get_connection_url())
        self.metadata = MetaData()
        self.messages_table = Table(
            os.getenv("AZR_DB_MESSAGES_TABLE", "messages_prod"), self.metadata,
            Column('id', UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4),
            Column('invoke_id', UNIQUEIDENTIFIER, primary_key=False, default=uuid.uuid4),
            Column('sender', String, nullable=False),
            Column('user_id', String, nullable=False),
            Column('user_type', String, nullable=False),
            Column('type', Enum('TEXT', 'AUDIO', 'IMAGE', name='message_type'), nullable=False),
            Column('message', String, nullable=True),
            Column('media_url', String, nullable=True),
            Column('payload', JSON, nullable=False),
            Column('content_filtered', Boolean, nullable=False, default=False),
            Column('model_data', JSON, nullable=True),
            Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
            Column('session_id', String, nullable=True),
            schema=os.getenv("AZR_DB_SCHEMA", "dbo")
        )
        self.metadata.create_all(self.engine)

    def create(self, payload):
        try:
            with self.engine.connect() as connection:
                with connection.begin():
                    cleaned_payload = dict(payload)
                    cleaned_payload.pop("contentFiltered", None)
                    cleaned_payload.pop("invokeId", None)
                    model_data = cleaned_payload.pop("modelData", None)
                    stmt = insert(self.messages_table).values(
                        id=uuid.uuid4(),
                        invoke_id=payload.get("invokeId", uuid.uuid4()),
                        sender=cleaned_payload.get("sender"),
                        user_id=cleaned_payload.get("user_id"),
                        user_type=cleaned_payload.get("type_user"),
                        type=cleaned_payload.get("type"),
                        message=cleaned_payload.get("message"),
                        payload=cleaned_payload,
                        media_url=cleaned_payload.get("mediaUrl"),
                        content_filtered=payload.get("contentFiltered", False),
                        model_data=model_data,
                        created_at=cleaned_payload.get("date", datetime.utcnow()),
                        session_id=cleaned_payload.get("session_id")
                    )
                    connection.execute(stmt)
        except Exception as e:
            logger.error(f"Error inserting message into database: {e}")