import random
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product, ProductStatus

CATEGORY_NAMES = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports & Outdoors",
    "Books",
    "Beauty & Personal Care",
    "Toys & Games",
    "Automotive",
    "Health & Wellness",
    "Groceries",
]

PRODUCT_PREFIXES = [
    "Premium",
    "Classic",
    "Pro",
    "Essential",
    "Ultra",
    "Compact",
    "Deluxe",
    "Smart",
    "Eco",
    "Daily",
]

PRODUCT_NAMES = [
    "Wireless Mouse",
    "Bluetooth Speaker",
    "Running Shoes",
    "Desk Lamp",
    "Coffee Maker",
    "Backpack",
    "Water Bottle",
    "Yoga Mat",
    "Notebook Set",
    "Phone Stand",
    "Kitchen Knife",
    "Sunglasses",
    "Fitness Tracker",
    "Board Game",
    "Car Charger",
    "Protein Powder",
    "Organic Snack Pack",
    "LED Monitor",
    "Winter Jacket",
    "Plant Pot",
    "Tennis Racket",
    "Novel Collection",
    "Face Cream",
    "Building Blocks",
    "Seat Cover",
]

DESCRIPTION_TEMPLATES = [
    "High-quality {name} designed for everyday use.",
    "Durable {name} with excellent value for money.",
    "Popular {name} loved by customers worldwide.",
    "Reliable {name} built with premium materials.",
    "Affordable {name} perfect for home and office.",
]

CATEGORY_COUNT = 10
PRODUCT_COUNT = 50


def _build_product_title() -> str:
    prefix = random.choice(PRODUCT_PREFIXES)
    name = random.choice(PRODUCT_NAMES)
    suffix = random.randint(100, 999)
    return f"{prefix} {name} {suffix}"


def _build_description(title: str) -> str:
    template = random.choice(DESCRIPTION_TEMPLATES)
    return template.format(name=title)[:500]


def seed_catalog(db: Session, *, fresh: bool = False) -> dict[str, int]:
    existing_categories = db.scalar(select(func.count()).select_from(Category)) or 0

    if existing_categories > 0 and not fresh:
        return {
            "categories": existing_categories,
            "products": db.scalar(select(func.count()).select_from(Product)) or 0,
            "skipped": True,
        }

    if fresh:
        db.execute(delete(Product))
        db.execute(delete(Category))
        db.flush()

    categories = [Category(name=name) for name in CATEGORY_NAMES[:CATEGORY_COUNT]]
    db.add_all(categories)
    db.flush()

    products: list[Product] = []
    for index in range(PRODUCT_COUNT):
        category = categories[index % len(categories)]
        title = _build_product_title()
        products.append(
            Product(
                category_id=category.id,
                title=title,
                description=_build_description(title),
                price=Decimal(str(round(random.uniform(5.0, 999.99), 2))),
                stock_quantity=random.randint(0, 500),
                status=random.choice(list(ProductStatus)),
            )
        )

    db.add_all(products)
    db.commit()

    return {
        "categories": len(categories),
        "products": len(products),
        "skipped": False,
    }
