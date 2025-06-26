from django.urls import path
from . import views

urlpatterns = [
    # Public list pages
    path('exercise-plans/', views.exercise_plan_list, name='exercise_plan_list'),
    path('nutrition-plans/', views.nutrition_plan_list, name='nutrition_plan_list'),
    path('products/', views.product_list, name='product_list'),
    path('', views.home, name='home'),

    # Detail pages
    path('exercise-plans/<int:pk>/', views.exercise_plan_detail, name='exercise_plan_detail'),
    path('nutrition-plans/<int:pk>/', views.nutrition_plan_detail, name='nutrition_plan_detail'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # NEW: Add to cart URL (requires item_type and pk)
    path('add-to-cart/<str:item_type>/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'), 
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('accounts/orders/', views.order_history, name='order_history'),
    path('subscribe/<str:item_type>/<int:pk>/', views.create_subscription_checkout, name='create_subscription_checkout'),

    # User authentication pages
    path('register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    
    #Subscribed Content URLs
    path('dashboard/', views.subscribed_dashboard, name='subscribed_dashboard'),
    path('exercise-plans/<int:pk>/content/', views.exercise_plan_content, name='exercise_plan_content'),
    path('nutrition-plans/<int:pk>/content/', views.nutrition_plan_content, name='nutrition_plan_content'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    #Staff-Only Dashboard URL
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
]
