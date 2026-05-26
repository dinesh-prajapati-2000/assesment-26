from openpyxl import Workbook
from app.models.product import Product


def generate_xlsx_file(items: list[Product]) -> bytes:
    wb = Workbook()
    wb.active
    wb.title = "Products"
    headers = ["ID", "Category", "Title", "Price", "Stock Quantity", "Status", "Created At"]
    ws = wb.active
    ws.append(headers)
    for item in items:
        ws.append([item.id, item.category.name, item.title, item.price, item.stock_quantity, item.status, item.created_at.date().strftime("%Y-%m-%d")])
    wb.save("products.xlsx")
    return "products.xlsx"