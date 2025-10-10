"""
URL configuration for MedShift Scheduler project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')), 
    path('dashboard/', include('apps.dashboard.urls')),
    path('employees/', include('apps.employees.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Customize admin site
admin.site.site_header = "MedShift Scheduler Administration"
admin.site.site_title = "MedShift Admin"
admin.site.index_title = "Welcome to MedShift Scheduler"