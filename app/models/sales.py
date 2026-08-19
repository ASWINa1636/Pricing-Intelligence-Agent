from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from app.database.connection import Base

class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    quantity = Column(Integer, nullable=False)
    selling_price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    promotion = Column(String)
    customer_segment = Column(String)
    channel = Column(String)
