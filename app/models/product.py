from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, index=True)
    subcategory = Column(String)
    brand = Column(String)
    cost_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    minimum_price = Column(Float)
    maximum_price = Column(Float)
    target_margin = Column(Float)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
