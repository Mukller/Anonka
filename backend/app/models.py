from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    threads = relationship("Thread", back_populates="user")


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_chat_id = Column(BigInteger, nullable=False)
    topic_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    sender_telegram_id = Column(BigInteger, nullable=False)
    sender_username = Column(String(255))
    message_text = Column(Text)
    attachments = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    thread = relationship("Thread", back_populates="messages")
    responses = relationship("Response", back_populates="message", cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    responder_user_id = Column(BigInteger, nullable=False)
    response_text = Column(Text)
    attachments = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="responses")


def get_engine(db_url: str):
    return create_engine(db_url, echo=False)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
