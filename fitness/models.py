from django.db import models
from django.contrib.auth.models import User


class ExercisePlan(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_weeks = models.PositiveIntegerField()
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    image = models.ImageField(upload_to='plan_images/', blank=True, null=True) # NEW FIELD

    def __str__(self):
        return self.title

class NutritionPlan(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_weeks = models.PositiveIntegerField()
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    image = models.ImageField(upload_to='plan_images/', blank=True, null=True) # NEW FIELD

    def __str__(self):
        return self.title

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True) # NEW FIELD

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_cost(self):
        # Calculate the total cost of all items in the cart
        return sum(item.get_total() for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=1)

    # Foreign keys to each type of purchasable item, allowing only one to be set
    exercise_plan = models.ForeignKey(ExercisePlan, on_delete=models.CASCADE, null=True, blank=True)
    nutrition_plan = models.ForeignKey(NutritionPlan, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)

    # Store the price at the time of addition to prevent price changes affecting existing cart items
    price_at_addition = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Ensure only one type of item is associated
        related_items = [self.exercise_plan, self.nutrition_plan, self.product]
        set_items = [item for item in related_items if item is not None]
        if len(set_items) > 1:
            raise ValueError("A CartItem can only be linked to one type of product.")

        # Set price_at_addition if not already set (e.g., when first adding to cart)
        if not self.price_at_addition:
            if self.exercise_plan:
                self.price_at_addition = self.exercise_plan.price
            elif self.nutrition_plan:
                self.price_at_addition = self.nutrition_plan.price
            elif self.product:
                self.price_at_addition = self.product.price

        super().save(*args, **kwargs)

    def get_item_object(self):
        """Returns the actual item object (ExercisePlan, NutritionPlan, or Product)."""
        if self.exercise_plan:
            return self.exercise_plan
        if self.nutrition_plan:
            return self.nutrition_plan
        if self.product:
            return self.product
        return None

    def get_total(self):
        # Calculate the total for this specific cart item line
        return self.quantity * self.price_at_addition

    def __str__(self):
        item_name = "Unknown Item"
        if self.exercise_plan:
            item_name = self.exercise_plan.title
        elif self.nutrition_plan:
            item_name = self.nutrition_plan.title
        elif self.product:
            item_name = self.product.name
        return f"{self.quantity} x {item_name} in Cart {self.cart.id}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    # Add status, shipping address, etc. later if needed

    class Meta:
        ordering = ['-order_date'] # Orders will be ordered by newest first

    def __str__(self):
        return f"Order {self.id} by {self.user.username} on {self.order_date.strftime('%Y-%m-%d')}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=50) # 'exercise_plan', 'nutrition_plan', 'product'
    item_id = models.PositiveIntegerField() # Stores the ID of the original item
    item_name = models.CharField(max_length=200) # Store name at time of order
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of order

    def __str__(self):
        return f"{self.quantity} x {self.item_name} for Order {self.order.id}"

    def get_total(self):
        return self.quantity * self.price

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    # A subscription should link to either an ExercisePlan or a NutritionPlan
    exercise_plan = models.ForeignKey(ExercisePlan, on_delete=models.SET_NULL, null=True, blank=True)
    nutrition_plan = models.ForeignKey(NutritionPlan, on_delete=models.SET_NULL, null=True, blank=True)

    # Stripe-related fields for managing the subscription via Stripe API
    stripe_subscription_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True) # Useful if not already on User model

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True) # Will be set for fixed-term subscriptions or after cancellation
    is_active = models.BooleanField(default=True)

    class Meta:
        # Enforce that a user can only subscribe to one specific plan once (unless it's expired)
        # This uniqueness constraint might need adjustment based on business logic (e.g., if re-subscribing)
        unique_together = ('user', 'exercise_plan', 'nutrition_plan')

    def __str__(self):
        plan_name = "Unknown Plan"
        if self.exercise_plan:
            plan_name = self.exercise_plan.title
        elif self.nutrition_plan:
            plan_name = self.nutrition_plan.title
        return f"{self.user.username}'s subscription to {plan_name} (Active: {self.is_active})"

    def save(self, *args, **kwargs):
        # Ensure only one type of plan is associated
        related_plans = [self.exercise_plan, self.nutrition_plan]
        set_plans = [plan for plan in related_plans if plan is not None]
        if len(set_plans) > 1:
            raise ValueError("A Subscription can only be linked to one type of plan (Exercise or Nutrition).")
        super().save(*args, **kwargs)
        

class Review(models.Model):
    # Foreign key to the User who wrote the review
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')

    # Foreign keys to each type of purchasable item, allowing only one to be set
    exercise_plan = models.ForeignKey(ExercisePlan, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    nutrition_plan = models.ForeignKey(NutritionPlan, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')

    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], # Rating from 1 to 5
        help_text="Rate this item on a scale of 1 to 5."
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Order reviews by newest first
        # Optional: Prevent a user from reviewing the same item multiple times
        # unique_together = ('user', 'exercise_plan', 'nutrition_plan', 'product') # This would prevent multiple reviews, might be too strict

    def __str__(self):
        item_name = "Unknown Item"
        if self.exercise_plan:
            item_name = self.exercise_plan.title
        elif self.nutrition_plan:
            item_name = self.nutrition_plan.title
        elif self.product:
            item_name = self.product.name
        return f"Review by {self.user.username} for {item_name} - {self.rating} stars"

    def save(self, *args, **kwargs):
        # Ensure only one type of item is associated with the review
        related_items = [self.exercise_plan, self.nutrition_plan, self.product]
        set_items = [item for item in related_items if item is not None]
        if len(set_items) > 1:
            raise ValueError("A Review can only be linked to one type of item (Exercise Plan, Nutrition Plan, or Product).")
        if not set_items:
            raise ValueError("A Review must be linked to an item.")
        super().save(*args, **kwargs)
