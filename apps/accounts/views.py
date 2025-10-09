"""
Authentication views for login, signup, password reset, etc.
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView
)

from .forms import (
    LoginForm,
    SignupForm,
    ForgotPasswordForm,
    ResetPasswordForm
)
from .models import User


class LoginView(FormView):
    """
    User login view.
    """
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard:home')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect to dashboard if already logged in
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        email = form.cleaned_data.get('username')  # Field is named 'username' but contains email
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me')
        
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            login(self.request, user)
            
            # Set session expiry
            if not remember_me:
                self.request.session.set_expiry(0)  # Session expires on browser close
            
            messages.success(
                self.request,
                _(f'Welcome back, {user.get_short_name()}!')
            )
            
            # Redirect to next parameter if exists
            next_url = self.request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            return redirect(self.success_url)
        else:
            messages.error(
                self.request,
                _('Invalid email or password.')
            )
            return self.form_invalid(form)


class SignupView(FormView):
    """
    User signup/registration view.
    """
    template_name = 'accounts/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect to dashboard if already logged in
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        
        messages.success(
            self.request,
            _(f'Account created successfully! Please log in.')
        )
        
        # Optionally: auto-login the user
        # login(self.request, user)
        # return redirect('dashboard:home')
        
        return redirect(self.success_url)


class ForgotPasswordView(PasswordResetView):
    """
    Password reset request view.
    """
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    email_template_name = 'emails/password_reset.html'
    subject_template_name = 'emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            _('Password reset instructions have been sent to your email.')
        )
        return super().form_valid(form)


class PasswordResetDoneView(TemplateView):
    """
    Password reset email sent confirmation.
    """
    template_name = 'accounts/password_reset_done.html'


class ResetPasswordView(PasswordResetConfirmView):
    """
    Password reset confirmation view.
    """
    template_name = 'accounts/reset_password.html'
    form_class = ResetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            _('Your password has been reset successfully! You can now log in.')
        )
        return super().form_valid(form)


class PasswordResetCompleteView(TemplateView):
    """
    Password reset complete confirmation.
    """
    template_name = 'accounts/password_reset_complete.html'


@login_required
def logout_view(request):
    """
    User logout view.
    """
    logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    return redirect('accounts:login')