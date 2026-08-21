from django.urls import path
from . import views

urlpatterns = [
    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "configuracion/correo/",
        views.configuracion_correo,
        name="configuracion_correo",
    ),

    path(
        "google/login/",
        views.google_login,
        name="google_login",
    ),

    path(
        "google/callback/",
        views.google_callback,
        name="google_callback",
    ),
]