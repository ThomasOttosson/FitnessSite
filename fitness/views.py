import os
from django.shortcuts import render, get_object_or_404, redirect
from .models import ExercisePlan, NutritionPlan, Product, Cart, CartItem, Order, OrderItem, Subscription
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
import stripe
from django.db.models import Q, Count, Avg
from .forms import ReviewForm, NewsletterForm, CustomUserCreationForm
import mailchimp_marketing as MailchimpClient
from mailchimp_marketing.api_client import ApiClientError
from django.conf import settings
from django.contrib.auth.models import User 

@login_required
def profile(request):
    # Fetch active subscriptions for the current user
    active_subscriptions = request.user.subscriptions.filter(is_active=True).select_related('exercise_plan', 'nutrition_plan')
    
    context = {
        'active_subscriptions': active_subscriptions,
    }
    # Ensure this points to the correct path, which is 'registration/profile.html' based on your structure
    return render(request, 'registration/profile.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # Use CustomUserCreationForm
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
        else:
            # Messages for form errors (Django's messages framework)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field.replace('password1', 'password').replace('password2', 'password confirmation')}: {error}")
    else:
        form = CustomUserCreationForm() # Use CustomUserCreationForm
    
    return render(request, 'registration/register.html', {'form': form})

def home(request):
    featured_products = Product.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )[:3]

    featured_exercise_plans = ExercisePlan.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )[:3]

    featured_nutrition_plans = NutritionPlan.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )[:3]

    context = {
        'featured_products': featured_products,
        'featured_exercise_plans': featured_exercise_plans,
        'featured_nutrition_plans': featured_nutrition_plans,
    }
    return render(request, 'public-pages/home.html', context)

def exercise_plan_list(request):
    plans = ExercisePlan.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    return render(request, 'public-pages/exercise_plan_list.html', {'plans': plans})

# Nutrition plans list view 
def nutrition_plan_list(request):
    plans = NutritionPlan.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    return render(request, 'public-pages/nutrition_plan_list.html', {'plans': plans})

# Products list view 
def product_list(request):
    products = Product.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    return render(request, 'public-pages/product_list.html', {'products': products})

# --- Detail Views for Each Item Type ---
def exercise_plan_detail(request, pk):
    plan = get_object_or_404(ExercisePlan, pk=pk)
    reviews = plan.reviews.all() # Fetch all reviews for this plan

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                review = form.save(commit=False)
                review.user = request.user
                review.exercise_plan = plan # Link review to the exercise plan
                review.save()
                messages.success(request, "Your review has been submitted!")
                return redirect('exercise_plan_detail', pk=pk) # Redirect to avoid resubmission
            else:
                messages.error(request, "You must be logged in to submit a review.")
        else:
            messages.error(request, "Please correct the errors in the review form.")
    else:
        form = ReviewForm() # Create a blank form for GET requests

    return render(request, 'public-pages/exercise_plan_detail.html', {'plan': plan, 'reviews': reviews, 'form': form})


def nutrition_plan_detail(request, pk):
    plan = get_object_or_404(NutritionPlan, pk=pk)
    reviews = plan.reviews.all() # Fetch all reviews for this plan

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                review = form.save(commit=False)
                review.user = request.user
                review.nutrition_plan = plan # Link review to the nutrition plan
                review.save()
                messages.success(request, "Your review has been submitted!")
                return redirect('nutrition_plan_detail', pk=pk)
            else:
                messages.error(request, "You must be logged in to submit a review.")
        else:
            messages.error(request, "Please correct the errors in the review form.")
    else:
        form = ReviewForm()

    return render(request, 'public-pages/nutrition_plan_detail.html', {'plan': plan, 'reviews': reviews, 'form': form})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all() # Fetch all reviews for this product

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                review = form.save(commit=False)
                review.user = request.user
                review.product = product # Link review to the product
                review.save()
                messages.success(request, "Your review has been submitted!")
                return redirect('product_detail', pk=pk)
            else:
                messages.error(request, "You must be logged in to submit a review.")
        else:
            messages.error(request, "Please correct the errors in the review form.")
    else:
        form = ReviewForm()

    return render(request, 'public-pages/product_detail.html', {'product': product, 'reviews': reviews, 'form': form})

@require_POST
@login_required
def add_to_cart(request, item_type, pk):
    item = None
    if item_type == 'exercise_plan':
        item = get_object_or_404(ExercisePlan, pk=pk)
    elif item_type == 'nutrition_plan':
        item = get_object_or_404(NutritionPlan, pk=pk)
    elif item_type == 'product':
        item = get_object_or_404(Product, pk=pk)
    else:
        messages.error(request, "Invalid item type for adding to cart.")
        return redirect('home')

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item = None
    if item_type == 'exercise_plan':
        cart_item, created = CartItem.objects.get_or_create(cart=cart, exercise_plan=item, defaults={'quantity': 0, 'price_at_addition': item.price})
    elif item_type == 'nutrition_plan':
        cart_item, created = CartItem.objects.get_or_create(cart=cart, nutrition_plan=item, defaults={'quantity': 0, 'price_at_addition': item.price})
    elif item_type == 'product':
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=item, defaults={'quantity': 0, 'price_at_addition': item.price})

    cart_item.quantity += 1
    cart_item.save()

    messages.success(request, f"'{cart_item.get_item_object()}' added to your cart!")
    return redirect('cart_detail')

# NEW: Cart Detail View
@login_required # Only logged-in users can view their cart
def cart_detail(request):
    cart = None
    try:
        cart = request.user.cart # Access the user's cart via the OneToOneField
    except Cart.DoesNotExist:
        pass # Cart does not exist for this user yet, it will be empty

    return render(request, 'registration/cart_detail.html', {'cart': cart})

@require_POST
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        cart_item.delete() # If quantity is 0 or less, remove the item
        messages.success(request, f"'{cart_item.get_item_object()}' removed from cart.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Quantity of '{cart_item.get_item_object()}' updated.")

    return redirect('cart_detail')

# NEW: Remove From Cart View
@require_POST
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item_name = cart_item.get_item_object() # Store name before deletion
    cart_item.delete()
    messages.success(request, f"'{item_name}' removed from cart.")
    return redirect('cart_detail')

@login_required # User must be logged in to checkout
def checkout(request):
    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect('cart_detail')

    if not cart.items.all():
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect('cart_detail')

    # Set your Stripe secret key
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    # Calculate total amount in cents (Stripe requires amount in smallest currency unit, e.g., cents for USD)
    # Ensure get_total_cost returns a Decimal
    total_amount = int(cart.get_total_cost() * 100) # Convert to cents

    # Create a PaymentIntent
    try:
        # Check if a PaymentIntent already exists for this cart (e.g., if user refreshes)
        # For simplicity, we'll create a new one each time for now.
        # In a real app, you might want to store the PI ID on the Cart or Order.
        intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency='usd', # Or your desired currency, e.g., 'eur'
            metadata={'cart_id': cart.id, 'user_id': request.user.id},
        )
        client_secret = intent.client_secret
    except stripe.error.StripeError as e:
        messages.error(request, f"Error creating payment intent: {e}")
        return redirect('cart_detail')

    stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')

    context = {
        'cart': cart,
        'stripe_publishable_key': stripe_publishable_key,
        'client_secret': client_secret, # Pass the client secret to the template
    }
    return render(request, 'registration/checkout.html', context)

@login_required
def payment_success(request):
    print("--- payment_success view accessed ---") # DEBUG
    session_id = request.GET.get('session_id') # For Checkout Sessions (subscriptions)
    payment_intent_client_secret = request.GET.get('payment_intent_client_secret') # For Payment Intents (one-time)

    print(f"DEBUG: session_id = {session_id}") # DEBUG
    print(f"DEBUG: payment_intent_client_secret = {payment_intent_client_secret}") # DEBUG

    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    # --- Step 1: Check for Subscription Checkout Session (session_id) first ---
    if session_id:
        print("DEBUG: session_id found. Attempting to retrieve Checkout Session.") # DEBUG
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            print(f"DEBUG: Checkout Session status = {checkout_session.payment_status}") # DEBUG

            if checkout_session.payment_status == 'paid':
                messages.success(request, "Your subscription has been activated successfully! 🎉")

                user = request.user
                item_type = checkout_session.metadata.get('item_type')
                item_id = checkout_session.metadata.get('item_id')

                plan = None
                if item_type == 'exercise_plan':
                    plan = get_object_or_404(ExercisePlan, pk=item_id)
                elif item_type == 'nutrition_plan':
                    plan = get_object_or_404(NutritionPlan, pk=item_id)

                if plan:
                    # Ensure we don't create duplicate subscriptions if user tries to re-subscribe to active plan
                    # A better approach might be to use get_or_create and check 'created' or update existing.
                    # For now, let's simplify and create new or retrieve existing, marking active.
                    subscription, created = Subscription.objects.get_or_create(
                        user=user,
                        exercise_plan=plan if item_type == 'exercise_plan' else None,
                        nutrition_plan=plan if item_type == 'nutrition_plan' else None,
                        defaults={
                            'stripe_subscription_id': checkout_session.subscription,
                            'stripe_customer_id': checkout_session.customer,
                            'is_active': True,
                        }
                    )
                    if not created:
                        subscription.stripe_subscription_id = checkout_session.subscription
                        subscription.stripe_customer_id = checkout_session.customer
                        subscription.is_active = True
                        subscription.save()
                        messages.info(request, "Existing subscription updated to active status.") # DEBUG message
                    print(f"DEBUG: Subscription created/updated: {subscription.id}, Created: {created}") # DEBUG

                else:
                    messages.warning(request, "Subscription plan not found in database for record keeping.")
                    print("DEBUG: Subscription plan not found in DB.") # DEBUG

                return render(request, 'registration/payment_success.html', {'status': 'success', 'subscription_flow': True})
            else:
                messages.error(request, "Subscription payment failed or was not completed. Please try again.")
                print(f"DEBUG: Checkout Session not 'paid': {checkout_session.payment_status}") # DEBUG
                return render(request, 'registration/payment_success.html', {'status': 'failure', 'subscription_flow': True})

        except stripe.error.StripeError as e:
            messages.error(request, f"Error retrieving subscription session: {e}")
            print(f"DEBUG: StripeError in session handling: {e}") # DEBUG
            return redirect('home')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during subscription processing: {e}")
            print(f"DEBUG: General Exception in session handling: {e}") # DEBUG
            return redirect('home')

    # --- Step 2: If no session_id, then check for PaymentIntent (for one-time purchases) ---
    elif payment_intent_client_secret:
        print("DEBUG: payment_intent_client_secret found. Attempting to retrieve PaymentIntent.") # DEBUG
        try:
            payment_intent = stripe.PaymentIntent.retrieve(
                payment_intent_client_secret.split('_secret_')[0]
            )
            print(f"DEBUG: PaymentIntent status = {payment_intent.status}") # DEBUG

            if payment_intent.status == 'succeeded':
                messages.success(request, "Your order has been placed successfully!")
                cart = None
                try:
                    cart = request.user.cart
                except Cart.DoesNotExist:
                    messages.error(request, "Could not find your cart to create an order.")
                    return redirect('home')

                if not cart.items.all():
                    messages.error(request, "Your cart was empty. No order created.")
                    return redirect('home')

                order = Order.objects.create(
                    user=request.user,
                    total_amount=cart.get_total_cost(),
                    stripe_payment_intent_id=payment_intent.id
                )

                for cart_item in cart.items.all():
                    item_obj = cart_item.get_item_object()
                    OrderItem.objects.create(
                        order=order,
                        item_type=(
                            'exercise_plan' if cart_item.exercise_plan
                            else 'nutrition_plan' if cart_item.nutrition_plan
                            else 'product'
                        ),
                        item_id=item_obj.id,
                        item_name=item_obj.title if hasattr(item_obj, 'title') else item_obj.name,
                        quantity=cart_item.quantity,
                        price=cart_item.price_at_addition
                    )

                cart.items.all().delete()
                cart.delete()

                return render(request, 'registration/payment_success.html', {'status': 'success'})
            elif payment_intent.status in ['processing', 'requires_action']:
                messages.info(request, "Your payment is still processing or requires further action. Please check back later.")
                return render(request, 'registration/payment_success.html', {'status': 'pending'})
            else:
                messages.error(request, "Payment failed or was cancelled. Please try again.")
                return render(request, 'registration/payment_success.html', {'status': 'failure'})

        except stripe.error.StripeError as e:
            messages.error(request, f"Error verifying payment: {e}")
            print(f"DEBUG: StripeError in PI handling: {e}") # DEBUG
            return redirect('cart_detail')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during order creation: {e}")
            print(f"DEBUG: General Exception in PI handling: {e}") # DEBUG
            return redirect('cart_detail')
    # --- Step 3: If neither session_id nor payment_intent_client_secret is present ---
    else:
        print("DEBUG: No session_id or payment_intent_client_secret found.") # DEBUG
        messages.error(request, "Invalid payment confirmation request: No payment information found.")
        return redirect('home')
    
@login_required
def order_history(request):
    # Fetch all orders for the current user, ordered by most recent first
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'registration/order_history.html', {'orders': orders})

@login_required
@require_POST # Should be a POST request from the detail page
def create_subscription_checkout(request, item_type, pk):
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    plan = None
    if item_type == 'exercise_plan':
        plan = get_object_or_404(ExercisePlan, pk=pk)
    elif item_type == 'nutrition_plan':
        plan = get_object_or_404(NutritionPlan, pk=pk)
    else:
        messages.error(request, "Invalid subscription type.")
        return redirect('home') # Or specific list page

    if not plan.stripe_price_id: # This now correctly expects a price_id
        messages.error(request, f"Subscription price ID not configured for {plan.title}.")
        return redirect(request.META.get('HTTP_REFERER', 'home')) # Redirect back

    try:
        # Create a Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[
            {
                'price': plan.stripe_price_id,
                'quantity': 1,
            },
        ],
        mode='subscription',
        # CRITICAL CORRECTION: Use concatenation to ensure {CHECKOUT_SESSION_ID} is a literal string
        success_url=request.build_absolute_uri('/payment-success/?session_id=') + '{CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/checkout/?cancelled=true'), # This one is already fine as it has no placeholder
        metadata={
            'user_id': request.user.id,
            'item_type': item_type,
            'item_id': plan.id,
        },
    )
        return redirect(checkout_session.url, code=303) # Redirect to Stripe Checkout page

    except stripe.error.StripeError as e:
        messages.error(request, f"Error creating Stripe checkout session: {e}")
        return redirect(request.META.get('HTTP_REFERER', 'home')) # Redirect back
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

def has_active_subscription(user, plan_type=None, plan_id=None):
    if not user.is_authenticated:
        return False

    subscriptions = user.subscriptions.filter(is_active=True)

    if plan_type == 'exercise_plan' and plan_id:
        return subscriptions.filter(exercise_plan__id=plan_id).exists()
    elif plan_type == 'nutrition_plan' and plan_id:
        return subscriptions.filter(nutrition_plan__id=plan_id).exists()
    elif plan_type is None and plan_id is None: # Check for ANY active subscription
        return subscriptions.exists()
    return False

@login_required
def subscribed_dashboard(request):
    if not has_active_subscription(request.user):
        messages.warning(request, "You need an active subscription to access the premium dashboard.")
        return redirect('home') # Or a page prompting subscription

    # You can fetch user's active subscriptions here to display them
    active_subscriptions = request.user.subscriptions.filter(is_active=True)
    return render(request, 'registration/subscribed_dashboard.html', {'active_subscriptions': active_subscriptions})

# NEW: Protected view for a specific subscribed Exercise Plan's content
@login_required
def exercise_plan_content(request, pk):
    plan = get_object_or_404(ExercisePlan, pk=pk)
    if not has_active_subscription(request.user, 'exercise_plan', plan.id):
        messages.error(request, f"You do not have an active subscription to '{plan.title}'.")
        return redirect('exercise_plan_detail', pk=pk) # Redirect to detail or subscription page

    return render(request, 'public-pages/exercise_plan_content.html', {'plan': plan})

# NEW: Protected view for a specific subscribed Nutrition Plan's content
@login_required
def nutrition_plan_content(request, pk):
    plan = get_object_or_404(NutritionPlan, pk=pk)
    if not has_active_subscription(request.user, 'nutrition_plan', plan.id):
        messages.error(request, f"You do not have an active subscription to '{plan.title}'.")
        return redirect('nutrition_plan_detail', pk=pk) # Redirect to detail or subscription page

    return render(request, 'public-pages/nutrition_plan_content.html', {'plan': plan})

# ... (all your existing views) ...

# NEW/UPDATED: Newsletter Signup View with Mailchimp Integration
def newsletter_signup(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                # Initialize Mailchimp Client
                client = MailchimpClient.Client()
                client.set_config({
                    "api_key": settings.MAILCHIMP_API_KEY,
                    "server": settings.MAILCHIMP_SERVER_PREFIX,
                })

                # Add member to Mailchimp audience
                # This method adds or updates a member. "subscribed" status.
                client.lists.add_list_member(settings.MAILCHIMP_AUDIENCE_ID, {
                    "email_address": email,
                    "status": "subscribed",
                })

                messages.success(request, "Thank you for subscribing to our newsletter!")

            except ApiClientError as error:
                error_json = error.text # Get the JSON response from Mailchimp
                # Example: {"detail": "Member exists", "status": 400}
                if "Member exists" in error_json:
                    messages.warning(request, "You are already subscribed to our newsletter.")
                else:
                    messages.error(request, f"Mailchimp Error: {error_json}")
                    print(f"Mailchimp API Error: {error_json}") # DEBUG
            except Exception as e:
                messages.error(request, f"An unexpected error occurred during subscription: {e}")
                print(f"General Error: {e}") # DEBUG

            return redirect(request.META.get('HTTP_REFERER', 'home')) 
        else:
            messages.error(request, "Please enter a valid email address.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home') 

@login_required
def staff_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have staff privileges to access this dashboard.")
        return redirect('home')

    # Fetch all users and prefetch their subscriptions to avoid N+1 queries
    all_users = User.objects.all().prefetch_related('subscriptions').order_by('username') # Order for consistency

    users_data = []
    subscribers_count = 0
    staff_count = 0
    active_users_count = 0 # Users marked as is_active=True

    for user_obj in all_users:
        # Determine if the user has any active subscription
        is_paying_subscriber = user_obj.subscriptions.filter(is_active=True).exists()

        # Build data-user-type string for front-end filtering
        user_type_data = []
        if is_paying_subscriber:
            user_type_data.append('subscriber')
        if user_obj.is_staff:
            user_type_data.append('staff')
        
        # Increment counts
        if is_paying_subscriber:
            subscribers_count += 1
        if user_obj.is_staff:
            staff_count += 1
        if user_obj.is_active:
            active_users_count += 1 


        users_data.append({
            'user': user_obj,
            'is_paying_subscriber': is_paying_subscriber,
            'data_user_type': ' '.join(user_type_data), # Join types for the data-attribute
        })

    context = {
        'users_data': users_data,
        'subscribers_count': subscribers_count,
        'staff_count': staff_count,
        'active_users_count': active_users_count,
    }
    return render(request, 'registration/staff_dashboard.html', context)

def custom_404_view(request, exception):
    return render(request, 'public-pages/404.html', {}, status=404)