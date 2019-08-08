from ninagram.views import handle_webhook
from django.urls import path

urlpatterns = [
    path('webhook/<str:token>/', handle_webhook),
]