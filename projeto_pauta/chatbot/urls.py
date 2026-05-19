# chatbot/urls.py

from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("popup/", views.chatbot_popup, name="popup"),
    path("responder/", views.chatbot_responder, name="responder"),
]