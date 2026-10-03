# generate_orders.py
import csv
import random
import os  # <--- Add this
from datetime import datetime, timedelta

# This creates the 'data' folder if it doesn't exist
os.makedirs('data', exist_ok=True) 

first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
last_names = ["Doe", "Smith", "Wilson", "Brown", "Davis", "Miller", "Moore", "Taylor", "Anderson", "Thomas"]
statuses = ["Processing", "Shipped", "Delivered", "Cancelled"]

with open('data/orders.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["order_id", "customer_email", "customer_name", "order_date", "status", "tracking_number", "total_amount"])
    
    for i in range(1000, 1100): # Generates ORD-1000 to ORD-1099
        first = random.choice(first_names)
        last = random.choice(last_names)
        email = f"{first.lower()}.{last.lower()}@example.com"
        name = f"{first} {last}"
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        status = random.choice(statuses)
        tracking = f"1Z{random.randint(1000000000, 9999999999)}" if status in ["Shipped", "Delivered"] else ""
        total = round(random.uniform(10.0, 500.0), 2)
        
        writer.writerow([f"ORD-{i}", email, name, date, status, tracking, total])

print("✅ Generated data/orders.csv with 100 realistic orders!")