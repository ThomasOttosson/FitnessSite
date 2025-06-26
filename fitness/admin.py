from django.contrib import admin
from .models import ExercisePlan, NutritionPlan, Product, Cart, CartItem, Order, OrderItem, Subscription, Review

admin.site.register(ExercisePlan)
admin.site.register(NutritionPlan)
admin.site.register(Product)
admin.site.register(Cart)     
admin.site.register(CartItem) 
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Subscription)
admin.site.register(Review)