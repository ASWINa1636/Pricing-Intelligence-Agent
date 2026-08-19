from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean
from app.database.connection import Base

class CompetitorPrice(Base):
    __tablename__ = "competitor_prices"

    observation_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    competitor = Column(String, index=True)
    competitor_price = Column(Float, nullable=False)
    availability = Column(Boolean, default=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    source = Column(String)
