# fitness/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import ExercisePlan, NutritionPlan, Product # Import your models

class StaticViewSitemap(Sitemap):
    # Sitemap for static pages like Home
    # You can set changefreq and priority based on how often content changes
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['home', 'exercise_plan_list', 'nutrition_plan_list', 'product_list']

    def location(self, item):
        return reverse(item)

class ExercisePlanSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return ExercisePlan.objects.all()

    def lastmod(self, obj):
        # If your models had an 'updated_at' field, you'd return it here
        # For simplicity, we don't have one, so we can omit or return None
        return None # Or obj.updated_at if you add that field

    def location(self, obj):
        return reverse('exercise_plan_detail', args=[obj.pk])

class NutritionPlanSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return NutritionPlan.objects.all()

    def lastmod(self, obj):
        return None # Or obj.updated_at

    def location(self, obj):
        return reverse('nutrition_plan_detail', args=[obj.pk])

class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return None # Or obj.updated_at

    def location(self, obj):
        return reverse('product_detail', args=[obj.pk])