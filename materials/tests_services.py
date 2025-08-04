from unittest.mock import patch

import stripe
from django.test import TestCase

from materials.services import StripeApiService


class StripeServiceTests(TestCase):
    @patch('stripe.Product.create')
    def test_create_stripe_product_success(self, mock_create):
        mock_create.return_value.id = 'prod_123'  # Имитация успешного ответа Stripe
        stripe_service = StripeApiService()
        product_id = stripe_service.get_create_stripe_product(
            MockCourse(name='Test Course') # Передаем как позиционный аргумент
        )
        self.assertEqual(product_id, 'prod_123')

    @patch('stripe.Product.create')
    def test_create_stripe_product_failure(self, mock_create):
        mock_create.side_effect = stripe.error.StripeError("Stripe API Error")  # Имитация ошибки Stripe
        stripe_service = StripeApiService()
        product_id = stripe_service.get_create_stripe_product(
            MockCourse(name='Test Course') # Передаем как позиционный аргумент
        )
        self.assertIsNone(product_id)  # Проверка, что при ошибке возвращается None

    @patch('stripe.Price.create')
    @patch('stripe.Product.retrieve')  # Мокируем stripe.Product.retrieve
    @patch('stripe.Product.create')
    def test_create_stripe_price_success(self, mock_product_create, mock_product_retrieve, mock_price_create):
        mock_product_create.return_value.id = 'prod_123'
        mock_product_retrieve.return_value.id = 'prod_123'  # Указываем, что retrieve возвращает объект с id = 'prod_123'
        mock_price_create.return_value.id = 'price_123'
        stripe_service = StripeApiService()
        course = MockCourse(name='Test Course', price=100)
        price_id = stripe_service.get_create_stripe_price(course)
        self.assertEqual(price_id, 'price_123')
        mock_price_create.assert_called()

    @patch('stripe.Price.create')
    @patch('stripe.Product.create')
    def test_create_stripe_price_failure(self, mock_product_create, mock_price_create):
        mock_product_create.return_value.id = 'prod_123'
        mock_price_create.side_effect = stripe.error.StripeError("Stripe API Error")
        stripe_service = StripeApiService()
        price_id = stripe_service.get_create_stripe_price(MockCourse(name='Test Course', price=100))
        self.assertIsNone(price_id)


# Для тестирования требуется мок-объект Product
class MockCourse:
    def __init__(self, name, price=None):
        self.name = name
        self.price = price
        self.stripe_product_id = None
        self.stripe_price_id = None

    def save(self):
        pass
