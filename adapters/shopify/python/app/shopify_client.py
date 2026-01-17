from __future__ import annotations

from typing import List, Optional

from .models import Product
class MockShopifyClient:
    """
    Mock catalog source. Later you'll replace this with a real Storefront API client.
    """

    def __post_init__(self) -> None:
        pass

    def list_products(self) -> List[Product]:
        return [
            Product(id="bouquet_roses", title="Bouquet of Red Roses", price=3500, currency="USD"),
            Product(id="tulips_yellow", title="Yellow Tulips", price=2800, currency="USD"),
            Product(id="orchid_white", title="White Orchid", price=4200, currency="USD"),
        ]

    def get_product(self, product_id: str) -> Optional[Product]:
        for p in self.list_products():
            if p.id == product_id:
                return p
        return None