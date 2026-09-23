"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Open the dashboard when visiting the root URL
    path(
        '',
        RedirectView.as_view(
            pattern_name='dashboard',
            permanent=False
        )
    ),

    path('', include('tracker.urls')),
]