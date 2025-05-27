from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'brands', views.BrandViewSet)
router.register(r'car-models', views.CarModelViewSet)
router.register(r'used-cars', views.UsedCarViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('', include(router.urls)),
]