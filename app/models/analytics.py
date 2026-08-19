from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base

class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    forecast_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    forecast_date = Column(DateTime(timezone=True), index=True)
    predicted_demand = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    model = Column(String)
    created_at = Column(DateTime(timezone=True), default=func.now())

class ElasticityResult(Base):
    __tablename__ = "elasticity_results"

    result_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    elasticity = Column(Float)
    r_squared = Column(Float)
    p_value = Column(Float)
    confidence_interval = Column(String)
    sample_size = Column(Integer)
    model_version = Column(String)
    created_at = Column(DateTime(timezone=True), default=func.now())

class PricingRecommendation(Base):
    __tablename__ = "pricing_recommendations"

    recommendation_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True)
    current_price = Column(Float)
    recommended_price = Column(Float)
    direction = Column(String)
    expected_demand = Column(Float)
    expected_revenue = Column(Float)
    expected_profit = Column(Float)
    expected_revenue_change = Column(Float)
    expected_profit_change = Column(Float)
    opportunity_score = Column(Float)
    confidence = Column(Float)
    explanation = Column(String)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=func.now())
