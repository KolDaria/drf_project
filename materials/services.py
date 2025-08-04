import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class StripeApiService:
    def __init__(self):
        self.api_key = getattr(settings, 'STRIPE_SECRET_KEY')
        stripe.api_key = self.api_key

        if not self.api_key:
            raise ImproperlyConfigured("STRIPE_SECRET_KEY должен быть установлен в настройках.")

    def get_create_stripe_product(self, instance):
        """
        Получает или создает продукт в Stripe для данного Course или Lesson.
        product_instance: Экземпляр Course или Lesson.
        Возвращает Stripe Product ID.
        """
        if hasattr(instance, 'stripe_product_id') and instance.stripe_product_id:
            # Если Stripe Product ID уже есть, пробуем его получить
            try:
                stripe.Product.retrieve(instance.stripe_product_id)
                return instance.stripe_product_id
            except stripe.error.InvalidRequestError:
                # Если продукт не найден в Stripe (например, был удален вручную),
                # создаем новый.
                pass
            except stripe.error.StripeError as e:
                print(f"Ошибка Stripe продукта {instance.stripe_product_id}: {e}")
                # В случае других ошибок Stripe, можем либо вернуть None, либо выбросить исключение
                return None  # Или raise e

        # Если Stripe Product ID нет или он невалиден, создаем новый продукт
        try:
            product = stripe.Product.create(name=instance.title if hasattr(instance, 'title') else instance.name)
            # Сохраняем новый Stripe Product ID в нашей модели
            instance.stripe_product_id = product.id
            instance.save()
            return product.id
        except stripe.error.StripeError as e:
            print(f"Ошибка создания Stripe продукта для {instance}: {e}")
            return None

    def get_create_stripe_price(self, instance):
        if instance.stripe_price_id:
            try:
                stripe.Price.retrieve(instance.stripe_price_id)
                return instance.stripe_price_id
            except stripe.error.InvalidRequestError:
                pass
            except stripe.error.StripeError as e:
                return None
        try:
            product_id = self.get_create_stripe_product(instance)
            if not product_id:
                return None

            # **Добавляем проверку существования product_id в Stripe:**
            try:
                stripe.Product.retrieve(product_id)
            except stripe.error.InvalidRequestError as e:
                instance.stripe_product_id = None  # Обнуляем product_id в базе данных
                instance.save()
                return self.get_create_stripe_price(instance)  # Рекурсивно вызываем функцию для создания всего заново
            except stripe.error.StripeError as e:
                return None

            price_in_cents = int(instance.price * 100)

            price = stripe.Price.create(
                unit_amount=price_in_cents,
                currency="rub",
                product=product_id,
            )
            instance.stripe_price_id = price.id
            instance.save()
            return price.id
        except stripe.error.StripeError as e:
            return None

    def create_stripe_checkout_session(self, price_id, success_url, cancel_url):
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return session  # Возвращаем объект сессии
        except stripe.error.StripeError as e:
            return None  # Возвращаем None в случае ошибки

    def retrieve_stripe_checkout_session(self, session_id):
        """
        Получает данные о сессии оформления заказа в Stripe по ID.
        Возвращает объект сессии Stripe.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            print(f"Извлечение ошибки Stripe сессии {session_id}: {e}")
            return None  # Возвращаем None в случае ошибки
