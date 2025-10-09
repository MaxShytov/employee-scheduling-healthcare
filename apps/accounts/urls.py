"""
URL configuration for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    
    # Password Reset
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('password-reset-done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.ResetPasswordView.as_view(), name='password_reset_confirm'),
    path('reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]