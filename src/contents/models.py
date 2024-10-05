from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class Author(models.Model):
    """
    TODO: When the data is being created or updated we don't know, need to add that information
    """
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    unique_id = models.CharField(max_length=1024, db_index=True, unique=True)
    url = models.CharField(max_length=1024, blank=True, )
    title = models.CharField(max_length=1024, blank=True, )
    big_metadata = models.JSONField(blank=True, null=True)
    secret_value = models.JSONField(blank=True, null=True)
    followers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Content(models.Model):
    """
    TODO: When the data is being created or updated we don't know, need to add that information
    """
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=1024, )
    url = models.CharField(max_length=1024, blank=True, )
    title = models.TextField(blank=True)
    like_count = models.BigIntegerField(blank=True, null=False, default=0, )
    comment_count = models.BigIntegerField(blank=True, null=False, default=0, )
    view_count = models.BigIntegerField(blank=True, null=False, default=0, )
    share_count = models.BigIntegerField(blank=True, null=False, default=0, )
    thumbnail_url = models.URLField(max_length=1024, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True, )
    big_metadata = models.JSONField(blank=True, null=True)
    secret_value = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    """
    TODO: The tag is being duplicated sometimes, need to do something in the database.
    Filtering
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)


class ContentTag(models.Model):
    """
    TODO: The content and tag is being duplicated, need to do something in the database
    """
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


# Written by Mahiuddin. Normalizing Start
class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255) # Storing password hashes in the same table is a security risk
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=20)
    is_admin = models.BooleanField(default=False)

    # TODO: Consult if additional fields should be added
    # is_verified = models.BooleanField(default=False)
    # updatedby, soft delete, is_active,

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.username

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Product(models.Model):
    product_id = models.IntegerField()  # Not unique, as it's repeated for each order
    product_name = models.CharField(max_length=255)
    product_description = models.TextField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2) # TODO: could be a separate model
    product_category = models.CharField(max_length=100) # TODO: could be a separate model
    product_subcategory = models.CharField(max_length=100)
    product_brand = models.CharField(max_length=100)
    product_stock = models.IntegerField()
    # product_ratings = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"{self.product_id} - {self.product_name}"

    class Meta:
        indexes = [
            models.Index(fields=["product_id"]),
        ]


class Order(models.Model):
    order_id = models.IntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_date = models.DateTimeField()
    order_status = models.CharField(max_length=50)
    shipping_method = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"{self.user} - Order {self.order_id}"

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["order_id"]),
            models.Index(fields=["tracking_number"]),
            models.Index(fields=["order_status"]), # TODO: Remove this index if not needed in report or query
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def _str_(self):
        return f"{self.order} - Order {self.product}"

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
            models.Index(fields=["item_price"]),
        ]

class Payment(models.Model):
    payment_id = models.CharField(max_length=100)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["payment_id"]),
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["payment_status"]), # TODO: Remove this index if not needed in report or query
        ]

class Supplier(models.Model):
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=255)
    supplier_contact_name = models.CharField(max_length=255)
    supplier_email = models.EmailField()
    supplier_phone = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["supplier_id"]),
        ]


class Warehouse(models.Model):
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255)
    warehouse_location = models.CharField(max_length=255)
    shelf_number = models.CharField(max_length=50)
    reorder_point = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["warehouse_id"]),
        ]

class SupportTicket(models.Model):
    # TODO: Could add a model for support ticket rating review
    support_ticket_id = models.IntegerField(null=True, blank=True)
    support_ticket_status = models.CharField(max_length=50, null=True, blank=True)
    support_agent_name = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["support_ticket_id"]),
        ]


class MarketingCampaign(models.Model):
    # TODO: Discount could be a separate model
    campaign_id = models.IntegerField(null=True, blank=True)
    campaign_name = models.CharField(max_length=255, null=True, blank=True)
    discount_code = models.CharField(max_length=50, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["campaign_id"]),
        ]

class WishList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def _str_(self):
        return f"{self.user.username} - Product {self.product.product_name}"

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["product"]),
        ]

class ReviewInformation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    review_text = models.TextField(null=True, blank=True)
    review_rating = models.IntegerField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["review_rating"]),
        ]

    # def save(self, *args, **kwargs):
    #     if self.review_rating:
    #         self.product.total_review_count += 1
    #         self.product.product_ratings = (
    #                                                self.product.product_ratings + self.review_rating
    #                                        ) / self.product.total_review_count
    #         self.product.save()
    #     super().save(*args, **kwargs)


# class MegaEcommerce(models.Model):
#     """
#     TODO: Normalize the model
#     """
#     # User Information
#     user_id = models.AutoField(primary_key=True)
#     username = models.CharField(max_length=100, unique=True)
#     email = models.EmailField(unique=True)
#     password_hash = models.CharField(max_length=255)  # Storing password hashes in the same table is a security risk
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     date_of_birth = models.DateField()
#     phone_number = models.CharField(max_length=20)
#     is_admin = models.BooleanField(default=False)
#
#     # Address Information (multiple addresses in one field)
#     addresses = models.JSONField(default=list)  # List of dictionaries containing address details
#
#     # Product Information
#     product_id = models.IntegerField()  # Not unique, as it's repeated for each order
#     product_name = models.CharField(max_length=255)
#     product_description = models.TextField()
#     product_price = models.DecimalField(max_digits=10, decimal_places=2)
#     product_category = models.CharField(max_length=100)
#     product_subcategory = models.CharField(max_length=100)
#     product_brand = models.CharField(max_length=100)
#     product_stock = models.IntegerField()
#     product_ratings = models.JSONField(default=list)  # List of dictionaries containing rating details
#
#     # Order Information
#     order_id = models.IntegerField()  # Not unique, as it's repeated for each product in the order
#     order_date = models.DateTimeField()
#     order_status = models.CharField(max_length=50)
#     shipping_method = models.CharField(max_length=100)
#     tracking_number = models.CharField(max_length=100, null=True, blank=True)
#
#     # Order Item Information
#     quantity = models.IntegerField()
#     item_price = models.DecimalField(max_digits=10, decimal_places=2)
#     discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#
#     # Payment Information
#     payment_id = models.CharField(max_length=100)
#     payment_method = models.CharField(max_length=50)
#     payment_status = models.CharField(max_length=50)
#     transaction_id = models.CharField(max_length=100, null=True, blank=True)
#
#     # Supplier Information
#     supplier_id = models.IntegerField()
#     supplier_name = models.CharField(max_length=255)
#     supplier_contact_name = models.CharField(max_length=255)
#     supplier_email = models.EmailField()
#     supplier_phone = models.CharField(max_length=20)
#
#     # Inventory Information
#     warehouse_id = models.IntegerField()
#     warehouse_name = models.CharField(max_length=255)
#     warehouse_location = models.CharField(max_length=255)
#     shelf_number = models.CharField(max_length=50)
#     reorder_point = models.IntegerField()
#
#     # Customer Service Information
#     support_ticket_id = models.IntegerField(null=True, blank=True)
#     support_ticket_status = models.CharField(max_length=50, null=True, blank=True)
#     support_agent_name = models.CharField(max_length=255, null=True, blank=True)
#
#     # Marketing Campaign Information
#     campaign_id = models.IntegerField(null=True, blank=True)
#     campaign_name = models.CharField(max_length=255, null=True, blank=True)
#     discount_code = models.CharField(max_length=50, null=True, blank=True)
#     discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
#
#     # Wishlist Information
#     wishlist_items = models.JSONField(default=list)  # List of product IDs
#
#     # Review Information
#     review_text = models.TextField(null=True, blank=True)
#     review_rating = models.IntegerField(null=True, blank=True)
#     review_date = models.DateTimeField(null=True, blank=True)
#
#     # Timestamp fields
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"{self.username} - Order {self.order_id} - Product {self.product_name}"
#
#     class Meta:
#         # This isn't a proper unique constraint, as it would prevent users from ordering the same product twice
#         # It's just to illustrate the complexity of the denormalized model
#         unique_together = ('user_id', 'order_id', 'product_id')
#         indexes = [
#             models.Index(fields=['username']),
#             models.Index(fields=['email']),
#             models.Index(fields=['order_id']),
#             models.Index(fields=['product_id']),
#             models.Index(fields=['payment_id']),
#         ]
