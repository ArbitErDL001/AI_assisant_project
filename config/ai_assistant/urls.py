from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.personality_login, name='personality_login'),
    path('', views.index, name='index'),
    path('ask/', views.ask_gemini, name='ask_gemini'),

    path(
        'service-worker.js',
        views.service_worker,
        name='service_worker',
    ),
]