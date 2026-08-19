from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ProductBase(BaseModel):
    product_id: str
    sku: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    cost_price: float
    current_price: float
    minimum_price: Optional[float] = None
    maximum_price: Optional[float] = None
    target_margin: Optional[float] = None
    stock_quantity: int = 0
    reorder_level: int = 0
    active: bool = True

class ProductResponse(ProductBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SaleBase(BaseModel):
    sale_id: str
    product_id: str
    timestamp: datetime
    quantity: int
    selling_price: float
    revenue: float
    cost: float
    profit: float
    discount: float = 0.0
    promotion: Optional[str] = None
    customer_segment: Optional[str] = None
    channel: Optional[str] = None

class SaleResponse(SaleBase):
    model_config = ConfigDict(from_attributes=True)

class CompetitorPriceBase(BaseModel):
    observation_id: str
    product_id: str
    competitor: str
    competitor_price: float
    availability: bool = True
    timestamp: datetime
    source: Optional[str] = None

class CompetitorPriceResponse(CompetitorPriceBase):
    model_config = ConfigDict(from_attributes=True)

class PricingRecommendationBase(BaseModel):
    recommendation_id: str
    product_id: str
    current_price: float
    recommended_price: float
    direction: str
    expected_demand: float
    expected_revenue: float
    expected_profit: float
    expected_revenue_change: float
    expected_profit_change: float
    opportunity_score: float
    confidence: float
    explanation: str
    status: str = "PENDING"

class PricingRecommendationResponse(PricingRecommendationBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
