
class Product:
    def __init__(self, name: str, price: float, quantity: int = 0):
        if price < 0:
            raise ValueError("Price cannot be negative")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        self.name = name
        self.price = price
        self.quantity = quantity

    def add_stock(self, amount: int):
        if amount < 0:
            raise ValueError("Cannot add negative stock")
        self.quantity += amount

    def remove_stock(self, amount: int):
        if amount < 0:
            raise ValueError("Cannot remove negative stock")
        if amount > self.quantity:
            raise ValueError("Not enough stock")
        self.quantity -= amount

    def is_available(self) -> bool:
        return self.quantity > 0

    def total_value(self) -> float:
        return self.price * self.quantity



import unittest

class TestProduct(unittest.TestCase):

    def setUp(self):
        self.product = Product("Book", 10.0, 5)

    def test_is_available_true(self):
        self.assertTrue(self.product.is_available())

    def test_is_available_false(self):
        p = Product("Empty", 10.0, 0)
        self.assertFalse(p.is_available())

    def test_add_stock(self):
        self.product.add_stock(5)
        self.assertEqual(self.product.quantity, 10)

    def test_remove_stock(self):
        self.product.remove_stock(2)
        self.assertEqual(self.product.quantity, 3)

    def test_total_value(self):
        self.assertEqual(self.product.total_value(), 50.0)

    def test_add_negative_stock_raises(self):
        with self.assertRaises(ValueError):
            self.product.add_stock(-1)

    def test_remove_too_much_stock_raises(self):
        with self.assertRaises(ValueError):
            self.product.remove_stock(100)

unittest.main(argv=[''], exit=False)




import pytest

@pytest.fixture
def product():
    return Product("Book", 10.0, 5)


def test_is_available(product):
    assert product.is_available() is True


def test_is_not_available():
    p = Product("Empty", 10.0, 0)
    assert p.is_available() is False


@pytest.mark.parametrize("amount,expected", [
    (5, 10),
    (1, 6),
    (0, 5),
])
def test_add_stock(product, amount, expected):
    product.add_stock(amount)
    assert product.quantity == expected


def test_remove_stock(product):
    product.remove_stock(2)
    assert product.quantity == 3


def test_total_value(product):
    assert product.total_value() == 50


def test_negative_price():
    with pytest.raises(ValueError):
        Product("Bad", -10, 1)


def test_remove_too_much(product):
    with pytest.raises(ValueError):
        product.remove_stock(999)