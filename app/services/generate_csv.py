import csv
from app.models.product import Product


def generate_csv_file(items: list[Product]) -> bytes:
    with open("products.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Category", "Title", "Price", "Stock Quantity", "Status", "Created At"])
        for item in items:
            writer.writerow([item.id, item.category.name, item.title, item.price, item.stock_quantity, item.status, item.created_at.date().strftime("%Y-%m-%d")])
    return "products.csv"