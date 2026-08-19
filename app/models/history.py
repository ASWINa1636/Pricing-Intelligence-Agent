from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base

class PriceHistory(Base):
    __tablename__ = "price_history"

    price_history_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    old_price = Column(Float)
    new_price = Column(Float, nullable=False)
    change_reason = Column(String)
    changed_by = Column(String)
    timestamp = Column(DateTime(timezone=True), default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String, primary_key=True, index=True)
    recommendation_id = Column(String, ForeignKey("pricing_recommendations.recommendation_id"), index=True)
    action = Column(String, nullable=False)
    user = Column(String)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    details = Column(String)
