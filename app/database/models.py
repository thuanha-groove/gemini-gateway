"""
Database models module.
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean

from app.database.base import Base


class Settings(Base):
    """
    Settings table, corresponding to configuration items in .env.
    """
    __tablename__ = "t_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, comment="Configuration item key name")
    value = Column(Text, nullable=True, comment="Configuration item value")
    description = Column(String(255), nullable=True, comment="Configuration item description")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="Creation time")
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="Update time")
    
    def __repr__(self):
        return f"<Settings(key='{self.key}', value='{self.value}')>"


class ErrorLog(Base):
    """
    Error log table.
    """
    __tablename__ = "t_error_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gemini_key = Column(String(100), nullable=True, comment="Gemini API key")
    model_name = Column(String(100), nullable=True, comment="Model name")
    error_type = Column(String(50), nullable=True, comment="Error type")
    error_log = Column(Text, nullable=True, comment="Error log")
    error_code = Column(Integer, nullable=True, comment="Error code")
    request_msg = Column(JSON, nullable=True, comment="Request message")
    request_time = Column(DateTime, default=datetime.datetime.now, comment="Request time")
    
    def __repr__(self):
        return f"<ErrorLog(id='{self.id}', gemini_key='{self.gemini_key}')>"


class RequestLog(Base):
    """
    API Request Log table.
    """

    __tablename__ = "t_request_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_time = Column(DateTime, default=datetime.datetime.now, comment="Request time")
    model_name = Column(String(100), nullable=True, comment="Model name")
    api_key = Column(String(100), nullable=True, comment="API key used")
    is_success = Column(Boolean, nullable=False, comment="Whether the request was successful")
    status_code = Column(Integer, nullable=True, comment="API response status code")
    latency_ms = Column(Integer, nullable=True, comment="Request latency (milliseconds)")

    def __repr__(self):
        return f"<RequestLog(id='{self.id}', key='{self.api_key[:4]}...', success='{self.is_success}')>"
