# mock_db.py

# The "Product Knowledge Graph"
PRODUCT_CATALOG = {
    "widget-x": {
        "name": "Industrial Widget X",
        "standard_price": 400.00,  # GBP
        "currency": "GBP",
        "variance_threshold": 0.15,  # 15%
        "primary_supplier": "supplier-a",
        "backup_suppliers": [
            "http://localhost:8000"  # This will be our Supplier B
        ]
    }
}

# The Corporate Spending Policy (AP2 Logic)
SPENDING_POLICY = {
    "max_variance": 0.15
}