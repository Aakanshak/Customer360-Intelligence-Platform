"""Deterministic enterprise-like demo data for local evaluation."""

import random
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from app.db.models import Customer, MarketingActivity, Product, SupportTicket, Transaction


def seed_demo_data(db: Session, customer_count: int = 250, seed: int = 42) -> dict:
    if db.query(Customer).count():
        return {"status": "skipped", "reason": "database already contains customers"}
    rng = np.random.default_rng(seed)
    random.seed(seed)
    now = datetime.utcnow()
    states = [("Maharashtra", "Mumbai"), ("Karnataka", "Bengaluru"), ("Delhi", "New Delhi"), ("Tamil Nadu", "Chennai"), ("West Bengal", "Kolkata")]
    product_specs = [
        (1, "Analytics Pro", "Software", 4999, 1700), (2, "Cloud Storage", "Software", 1999, 550),
        (3, "Smart Watch", "Electronics", 7999, 4200), (4, "Headphones", "Electronics", 3499, 1800),
        (5, "Office Chair", "Furniture", 11999, 6800), (6, "Desk Lamp", "Furniture", 2499, 1100),
    ]
    products = [Product(product_id=p[0], product_name=p[1], category=p[2], unit_price=p[3], unit_cost=p[4]) for p in product_specs]
    db.add_all(products)
    db.flush()
    tx_id = campaign_id = ticket_id = 1
    transactions = []
    campaigns = []
    tickets = []
    first_names = ["Aarav", "Aditi", "Arjun", "Diya", "Ishaan", "Kavya", "Meera", "Neha", "Rohan", "Vihaan"]
    last_names = ["Sharma", "Patel", "Singh", "Iyer", "Gupta", "Das", "Khan", "Reddy"]
    for customer_id in range(1, customer_count + 1):
        state, city = random.choice(states)
        signup_days = int(rng.integers(180, 1200))
        gender = random.choice(["Female", "Male", "Non-binary"])
        customer = Customer(
            customer_id=customer_id, name=f"{random.choice(first_names)} {random.choice(last_names)}",
            age=int(rng.integers(18, 75)), gender=gender, city=city, state=state,
            signup_date=(now - timedelta(days=signup_days)).date(),
            email=f"customer{customer_id}@example.com", is_active=True,
        )
        db.add(customer)
        latent_value = rng.gamma(2.0, 2.2)
        churn_prone = rng.random() < 0.28
        order_count = int(min(rng.poisson(latent_value), 24))
        for _ in range(order_count):
            product = random.choice(product_specs)
            max_recency = 420 if churn_prone else 100
            days_ago = int(rng.integers(2, min(signup_days, max_recency) + 1))
            quantity = int(rng.integers(1, 4))
            discount = float(random.choice([0, 0, 0, product[3] * 0.05, product[3] * 0.10]))
            transactions.append(Transaction(
                transaction_id=tx_id, customer_id=customer_id, product_id=product[0], quantity=quantity,
                order_amount=float(product[3] * quantity - discount), cost_amount=float(product[4] * quantity),
                discount_amount=discount, order_date=now - timedelta(days=days_ago),
                channel=random.choice(["Web", "Mobile", "Store"]), status="completed",
            ))
            tx_id += 1
        for _ in range(int(rng.integers(0, 5))):
            campaigns.append(MarketingActivity(
                campaign_id=campaign_id, customer_id=customer_id, campaign_name=random.choice(["Festive", "Winback", "New Product"]),
                campaign_response=bool(rng.random() < (0.45 if not churn_prone else 0.15)), channel=random.choice(["Email", "SMS", "Social"]),
                campaign_cost=float(rng.uniform(10, 80)), touched_at=now - timedelta(days=int(rng.integers(1, 365))),
            ))
            campaign_id += 1
        for _ in range(int(rng.poisson(0.8))):
            resolution = float(rng.uniform(1, 72))
            opened = now - timedelta(days=int(rng.integers(1, 365)))
            tickets.append(SupportTicket(
                ticket_id=ticket_id, customer_id=customer_id, issue_type=random.choice(["Billing", "Delivery", "Product", "Account"]),
                resolution_time=resolution, ticket_status="closed", satisfaction_score=round(float(rng.uniform(1, 5)), 1),
                opened_at=opened, closed_at=opened + timedelta(hours=resolution),
            ))
            ticket_id += 1
    db.add_all(transactions + campaigns + tickets)
    db.commit()
    return {"status": "created", "customers": customer_count, "transactions": len(transactions), "campaigns": len(campaigns), "tickets": len(tickets)}
