"""
URL configuration for core app.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.help_page, name='help'),
]