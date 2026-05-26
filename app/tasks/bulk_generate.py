

from faker import Faker

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.product import Product, ProductStatus

batch_size = 1000

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def bulk_generate_products_task(self,category_id: int, count: int):
    print(f"Generating {count} products for category {category_id}")
    db = SessionLocal()
    fake = Faker()
    products = []
    for _ in range(count):
        products.append(
            {
                "category_id": category_id,
                "title": fake.name(),
                "description": fake.text(),
                "price": fake.random_int(min=100, max=1000),
                "stock_quantity": fake.random_int(min=100, max=1000),
                "status": ProductStatus.ACTIVE,
            }
        )

    try:
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            db.bulk_insert_mappings(Product,batch)
            db.commit()
        return {
            "success": True,
            "message": "Products generated successfully",
        }
    except Exception as e:
        print(e)
        db.rollback()
        raise e
    finally:
        db.close()
