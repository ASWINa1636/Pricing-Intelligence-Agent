import os
import sys
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine, SessionLocal
from app.models import Base, Product, Sale, CompetitorPrice
from sqlalchemy.orm import Session

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

CATEGORIES = {
    "Laptops": {"cost_range": (300, 1500), "margin": 0.15, "elasticity": -1.8, "brands": ["TechBook", "LapMaster", "GamerPro"]},
    "Monitors": {"cost_range": (80, 500), "margin": 0.20, "elasticity": -1.5, "brands": ["ViewTech", "ClearDisplay", "PixelPerfect"]},
    "Smartphones": {"cost_range": (200, 800), "margin": 0.12, "elasticity": -1.2, "brands": ["CellularPro", "MobiTech", "SmartConnect"]},
    "Headphones": {"cost_range": (20, 200), "margin": 0.35, "elasticity": -2.2, "brands": ["AudioBlast", "SoundWave", "QuietListen"]},
    "Keyboards": {"cost_range": (15, 100), "margin": 0.40, "elasticity": -2.0, "brands": ["TypeFast", "ClickyMech", "ErgoType"]},
    "Mice": {"cost_range": (10, 80), "margin": 0.40, "elasticity": -1.9, "brands": ["PointPrecision", "GamerMouse", "ErgoClick"]},
    "Tablets": {"cost_range": (150, 600), "margin": 0.18, "elasticity": -1.4, "brands": ["TabMaster", "PadTech", "SlatePro"]},
    "Smartwatches": {"cost_range": (80, 300), "margin": 0.25, "elasticity": -1.6, "brands": ["WristTech", "TimeSmart", "FitTracker"]},
    "Speakers": {"cost_range": (30, 250), "margin": 0.30, "elasticity": -1.7, "brands": ["BoomBox", "LoudSound", "HomeAudio"]},
    "Accessories": {"cost_range": (5, 50), "margin": 0.50, "elasticity": -2.5, "brands": ["ChargeIt", "CablePro", "ProtectCase"]},
}

COMPETITORS = ["CompA", "CompB", "CompC"]

def generate_products(num_products=1000):
    products = []
    print(f"Generating {num_products} products...")
    for i in range(num_products):
        category_name = random.choice(list(CATEGORIES.keys()))
        cat_info = CATEGORIES[category_name]
        
        cost = round(random.uniform(*cat_info["cost_range"]), 2)
        price = round(cost / (1 - cat_info["margin"]), 2)
        min_price = round(cost * 1.05, 2)  # at least 5% margin
        max_price = round(price * 1.5, 2)
        
        product_id = f"PROD_{uuid.uuid4().hex}"
        sku = f"{category_name[:3].upper()}_{i:04d}"
        
        products.append(Product(
            product_id=product_id,
            sku=sku,
            product_name=f"{random.choice(cat_info['brands'])} {category_name[:-1]} Model {random.randint(100,999)}",
            category=category_name,
            brand=random.choice(cat_info['brands']),
            cost_price=cost,
            current_price=price,
            minimum_price=min_price,
            maximum_price=max_price,
            target_margin=cat_info["margin"],
            stock_quantity=random.randint(50, 1000),
            reorder_level=random.randint(10, 50)
        ))
    return products

def generate_sales_and_competitors(products, weeks=52):
    sales = []
    comp_prices = []
    
    print(f"Generating {weeks} weeks of sales history for {len(products)} products...")
    
    # 52 weeks back from today
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    date_list = [start_date + timedelta(weeks=x) for x in range(weeks)]
    
    for p in products:
        base_demand = random.uniform(50, 500)
        elasticity = CATEGORIES[p.category]["elasticity"] + random.uniform(-0.2, 0.2)
        
        for d in date_list:
            # Introduce seasonal noise (e.g. holiday bump in nov/dec)
            seasonality = 1.0
            if d.month in [11, 12]:
                seasonality = 1.3
                
            # Random price variation (simulating past pricing tests)
            price_multiplier = random.uniform(0.85, 1.15)
            historical_price = round(p.current_price * price_multiplier, 2)
            
            # log(Q) = alpha + beta * log(P) + noise -> Q = exp(alpha) * P^beta * exp(noise)
            # base_demand corresponds to demand at target price
            demand_multiplier = (historical_price / p.current_price) ** elasticity
            noise = np.random.normal(1, 0.1)
            
            quantity = int(base_demand * demand_multiplier * seasonality * noise)
            quantity = max(1, quantity)
            
            revenue = round(quantity * historical_price, 2)
            cost = round(quantity * p.cost_price, 2)
            profit = round(revenue - cost, 2)
            
            sales.append(Sale(
                sale_id=f"SALE_{uuid.uuid4().hex}",
                product_id=p.product_id,
                timestamp=d,
                quantity=quantity,
                selling_price=historical_price,
                revenue=revenue,
                cost=cost,
                profit=profit
            ))
            
            # Competitor prices
            for comp in COMPETITORS:
                # randomly competitor is cheaper or more expensive
                comp_mult = random.uniform(0.9, 1.1)
                comp_prices.append(CompetitorPrice(
                    observation_id=f"COMP_{uuid.uuid4().hex}",
                    product_id=p.product_id,
                    competitor=comp,
                    competitor_price=round(historical_price * comp_mult, 2),
                    timestamp=d
                ))
                
    return sales, comp_prices

def main():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    products = generate_products(1000)
    db.bulk_save_objects(products)
    db.commit()
    print(f"Inserted {len(products)} products.")
    
    sales, comp_prices = generate_sales_and_competitors(products, weeks=52)
    
    # Bulk insert in chunks to avoid memory issues
    chunk_size = 10000
    for i in range(0, len(sales), chunk_size):
        db.bulk_save_objects(sales[i:i+chunk_size])
    db.commit()
    print(f"Inserted {len(sales)} sales records.")
    
    for i in range(0, len(comp_prices), chunk_size):
        db.bulk_save_objects(comp_prices[i:i+chunk_size])
    db.commit()
    print(f"Inserted {len(comp_prices)} competitor price records.")
    
    db.close()
    print("Data generation complete!")

if __name__ == "__main__":
    main()
