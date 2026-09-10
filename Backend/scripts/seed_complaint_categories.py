"""Seed the initial complaint categories and subcategories.

Usage (from Backend/):
    venv/Scripts/python.exe -m scripts.seed_complaint_categories

Idempotent: existing categories (matched by key) are left as-is, new ones added.
Legacy categories are marked inactive.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.complaint_category import ComplaintCategory
from app.models.complaint_subcategory import ComplaintSubcategory
import uuid

CATEGORIES_MAP = {
    "package_food": {
        "name": "Package Food",
        "subs": ["Dairy products", "Fats & oils", "Edible ices including sorbet", "Confectionery", "Cereal & cereal products", "Bakery products", "Meat & meat products including poultry", "Fish & fish products", "Egg & egg products", "Sweetners including honey", "Salt/spices/soups/sauces/salads & protein products", "Beverages excluding dairy products", "Ready to eat savouries", "Prepared food", "Others", "Nutraceuticals", "Fruit and Vegetables", "Ayurveda Aahara"]
    },
    "catering_premises": {
        "name": "Food Catering Premises",
        "subs": ["Restaurants", "Canteen", "Cafeteria", "Dhabas", "Cafe", "Hostel Mess", "Food Trucks", "Take aways", "Hotel", "Others"]
    },
    "ecommerce": {
        "name": "Online aggregator/e-commerce",
        "subs": ["Prepared Food Delivering Agency", "Grocery Delivering Agency", "Others"]
    },
    "retailer_premises": {
        "name": "Retailer Premises",
        "subs": ["Retail shops", "Milk & milk products retail shop", "Meat & meat products (including poultry & fish) retail shop", "Fruits & vegetable retail shop", "Others"]
    },
    "others": {
        "name": "Others",
        "subs": []
    }
}

def seed_categories(db) -> None:
    # Set legacy categories to inactive
    legacy_keys = ["expired_food", "unhygienic_premises", "spoiled_food", "contamination", "improper_storage", "other"]
    legacy_cats = db.execute(select(ComplaintCategory).where(ComplaintCategory.key.in_(legacy_keys))).scalars().all()
    for lc in legacy_cats:
        if lc.is_active:
            lc.is_active = False
            print(f"deactivated legacy category {lc.key}")
    db.commit()

    for key, data in CATEGORIES_MAP.items():
        name = data["name"]
        subs = data["subs"]
        
        category = db.execute(select(ComplaintCategory).where(ComplaintCategory.key == key)).scalar_one_or_none()
        if category is None:
            category = ComplaintCategory(key=key, name=name, description="")
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"created category {key} - {name}")
        else:
            if not category.is_active:
                category.is_active = True
                db.commit()
            print(f"category {key} already exists")

        # Seed subcategories
        for sub_name in subs:
            sub_key = sub_name.lower().replace(" ", "_").replace("&", "and").replace("/", "_").replace("(", "").replace(")", "").replace("-", "_")
            if len(sub_key) > 50:
                sub_key = sub_key[:50]
                
            subcat = db.execute(select(ComplaintSubcategory).where(
                ComplaintSubcategory.category_id == category.id,
                ComplaintSubcategory.key == sub_key
            )).scalar_one_or_none()
            
            if subcat is None:
                subcat = ComplaintSubcategory(
                    category_id=category.id,
                    key=sub_key,
                    name=sub_name,
                )
                db.add(subcat)
                db.commit()
                print(f"  created subcategory {sub_key} - {sub_name}")


def main() -> None:
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
