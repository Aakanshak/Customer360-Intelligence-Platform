"""Normalized operational model plus persisted analytical outputs."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(32))
    city: Mapped[str | None] = mapped_column(String(128))
    state: Mapped[str | None] = mapped_column(String(128), index=True)
    signup_date: Mapped[date] = mapped_column(Date, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    marketing: Mapped[list["MarketingActivity"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    support_tickets: Mapped[list["SupportTicket"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(128), index=True)
    unit_price: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float] = mapped_column(Float)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_customer_date", "customer_id", "order_date"),)

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.product_id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    order_amount: Mapped[float] = mapped_column(Float)
    cost_amount: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    order_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    channel: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="completed")

    customer: Mapped[Customer] = relationship(back_populates="transactions")
    product: Mapped[Product | None] = relationship()


class MarketingActivity(Base):
    __tablename__ = "marketing_activities"

    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    campaign_name: Mapped[str | None] = mapped_column(String(128))
    campaign_response: Mapped[bool] = mapped_column(Boolean, default=False)
    channel: Mapped[str | None] = mapped_column(String(64))
    campaign_cost: Mapped[float] = mapped_column(Float, default=0)
    touched_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    customer: Mapped[Customer] = relationship(back_populates="marketing")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    issue_type: Mapped[str | None] = mapped_column(String(128))
    resolution_time: Mapped[float | None] = mapped_column(Float)
    ticket_status: Mapped[str] = mapped_column(String(64), default="closed")
    satisfaction_score: Mapped[float | None] = mapped_column(Float)
    opened_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    customer: Mapped[Customer] = relationship(back_populates="support_tickets")


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    batch_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_type: Mapped[str] = mapped_column(String(32), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    checksum: Mapped[str] = mapped_column(String(64), unique=True)
    row_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    quality_report: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModelRun(Base):
    __tablename__ = "model_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    model_type: Mapped[str] = mapped_column(String(64), index=True)
    model_name: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32))
    metrics_json: Mapped[str] = mapped_column(Text)
    artifact_path: Mapped[str | None] = mapped_column(String(512))
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
