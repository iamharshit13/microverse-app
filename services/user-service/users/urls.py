from django.urls import path
from .views import RegisterView, LoginView, home_view

urlpatterns = [
    path('', home_view, name='home'),  # This will be available at /api/user/
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]
