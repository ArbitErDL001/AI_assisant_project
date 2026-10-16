from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView\

urlpatterns = [
    path(
        '', RedirectView.as_view(
            pattern_name='personilty_login', permanent=False,
        ),
        name='root',
    ),
    path('admin/', admin.site.urls),
    path('ai_assistant/', include('ai_assistant.urls')),
]