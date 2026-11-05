from decimal import Decimal

from argon2 import PasswordHasher
from sqlalchemy import select

from app.database.models import Inventory, Product, Role, User
from app.database.session import SessionLocal

password_hasher = PasswordHasher()

ROLE_NAMES = ("ADMIN", "INVENTORY_MANAGER", "CUSTOMER")
SEED_USERS = (
    ("admin@orderflow.local", "Admin", "User", "Admin123!"),
    ("inventory@orderflow.local", "Inventory", "Manager", "Inventory123!"),
    ("customer1@orderflow.local", "Demo", "Customer", "Customer123!"),
    ("customer2@orderflow.local", "Second", "Customer", "Customer123!"),
)
PRODUCTS = (
    ("ELEC-001", "Wireless Headphones", "Audio", "89.99"),
    ("ELEC-002", "Mechanical Keyboard", "Audio", "129.00"),
    ("ELEC-003", "USB-C Dock", "Electronics", "74.50"),
    ("ELEC-004", "4K Monitor", "Electronics", "399.99"),
    ("ELEC-005", "Webcam Pro", "Electronics", "59.95"),
    ("HOME-001", "Desk Lamp", "Home Office", "34.99"),
    ("HOME-002", "Ergonomic Chair", "Home Office", "249.00"),
    ("HOME-003", "Standing Desk Mat", "Home Office", "45.00"),
    ("HOME-004", "Cable Organizer", "Home Office", "12.99"),
    ("HOME-005", "Notebook Set", "Stationery", "18.50"),
    ("LIFE-001", "Insulated Bottle", "Lifestyle", "24.99"),
    ("LIFE-002", "Travel Backpack", "Lifestyle", "79.00"),
    ("LIFE-003", "Fitness Tracker", "Lifestyle", "119.99"),
    ("LIFE-004", "Yoga Mat", "Lifestyle", "29.95"),
    ("LIFE-005", "Running Cap", "Lifestyle", "16.00"),
    ("BOOK-001", "Python Systems Design", "Books", "42.00"),
    ("BOOK-002", "Modern Database Patterns", "Books", "51.25"),
    ("BOOK-003", "Product Leadership", "Books", "38.75"),
    ("FOOD-001", "Specialty Coffee", "Food", "22.00"),
    ("FOOD-002", "Tea Collection", "Food", "19.50"),
    ("COMP-001", "ProBook 14 Laptop", "Computers and Laptops", "1299.00"),
    ("COMP-002", "Creator Laptop 16", "Computers and Laptops", "1899.00"),
    ("COMP-003", "UltraWide Display", "Computers and Laptops", "649.00"),
    ("COMP-004", "Mini Desktop PC", "Computers and Laptops", "799.00"),
    ("COMP-005", "Thunderbolt Hub", "Computers and Laptops", "149.00"),
    ("MOB-001", "Pixel Pro Smartphone", "Mobile Phones", "899.00"),
    ("MOB-002", "Galaxy Note Ultra", "Mobile Phones", "1099.00"),
    ("MOB-003", "Foldable Phone Case", "Mobile Phones", "39.99"),
    ("MOB-004", "Fast Charge Adapter", "Mobile Phones", "29.99"),
    ("MOB-005", "MagSafe Battery Pack", "Mobile Phones", "89.99"),
    ("ACC-001", "Wireless Mouse", "Accessories", "39.99"),
    ("ACC-002", "Low Profile Keyboard", "Accessories", "99.00"),
    ("ACC-003", "Noise Cancelling Buds", "Accessories", "149.00"),
    ("ACC-004", "Laptop Stand", "Accessories", "54.00"),
    ("ACC-005", "HDMI Cable Pro", "Accessories", "18.99"),
    ("OFF-001", "Laser Printer", "Office Equipment", "299.00"),
    ("OFF-002", "Document Scanner", "Office Equipment", "229.00"),
    ("OFF-003", "Conference Speaker", "Office Equipment", "179.00"),
    ("OFF-004", "Whiteboard Planner", "Office Equipment", "69.00"),
    ("OFF-005", "Desk Organizer", "Office Equipment", "31.00"),
    ("NET-001", "Wi-Fi 6 Router", "Networking Equipment", "189.00"),
    ("NET-002", "Managed Network Switch", "Networking Equipment", "249.00"),
    ("NET-003", "Mesh Wi-Fi System", "Networking Equipment", "329.00"),
    ("NET-004", "USB Network Adapter", "Networking Equipment", "24.99"),
    ("NET-005", "Fiber Media Converter", "Networking Equipment", "74.99"),
    ("STO-001", "Portable SSD 1TB", "Storage Devices", "99.00"),
    ("STO-002", "Portable SSD 2TB", "Storage Devices", "179.00"),
    ("STO-003", "NAS Storage 4 Bay", "Storage Devices", "599.00"),
    ("STO-004", "Secure USB Drive", "Storage Devices", "49.99"),
    ("STO-005", "Memory Card 512GB", "Storage Devices", "69.99"),
    ("SMT-001", "Smart Home Hub", "Smart Devices", "129.00"),
    ("SMT-002", "Indoor Security Camera", "Smart Devices", "79.00"),
    ("SMT-003", "Smart LED Light Kit", "Smart Devices", "59.00"),
    ("SMT-004", "Voice Assistant Speaker", "Smart Devices", "99.00"),
    ("SMT-005", "Smart Thermostat", "Smart Devices", "199.00"),
)

IMAGE_BY_CATEGORY = {
    "Computers and Laptops": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900&q=85",
    "Mobile Phones": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=900&q=85",
    "Accessories": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=900&q=85",
    "Electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=900&q=85",
    "Audio": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&q=85",
    "Office Equipment": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=900&q=85",
    "Home Office": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=900&q=85",
    "Furniture": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=900&q=85",
    "Networking Equipment": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=900&q=85",
    "Storage Devices": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=900&q=85",
    "Smart Devices": "https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=900&q=85",
    "Lifestyle": "https://images.unsplash.com/photo-1511556820780-d912e42b4980?w=900&q=85",
    "Books": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=900&q=85",
    "Food": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900&q=85",
    "Stationery": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=900&q=85",
}


def seed() -> None:
    with SessionLocal.begin() as db:
        roles = {
            role.name: role
            for role in db.scalars(select(Role).where(Role.name.in_(ROLE_NAMES))).all()
        }
        for role_name in ROLE_NAMES:
            if role_name not in roles:
                roles[role_name] = Role(name=role_name)
                db.add(roles[role_name])
        db.flush()

        for email, first_name, last_name, password in SEED_USERS:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    password_hash=password_hasher.hash(password),
                    first_name=first_name,
                    last_name=last_name,
                    roles=[roles["ADMIN" if email.startswith("admin") else
                           "INVENTORY_MANAGER" if email.startswith("inventory") else "CUSTOMER"]],
                )
                db.add(user)

        db.flush()
        for sku, name, category, price in PRODUCTS:
            product = db.scalar(select(Product).where(Product.sku == sku))
            if product is None:
                product = Product(
                    sku=sku,
                    name=name,
                    category=category,
                    price=Decimal(price),
                    description=f"{name} from the OrderFlow development catalogue.",
                    image_url=IMAGE_BY_CATEGORY.get(category),
                )
                product.inventory = Inventory(quantity=100, low_stock_threshold=10)
                db.add(product)
            else:
                product.image_url = IMAGE_BY_CATEGORY.get(category)


if __name__ == "__main__":
    seed()
    print("OrderFlow development data seeded.")
