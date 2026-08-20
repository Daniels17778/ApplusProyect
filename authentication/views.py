from django.shortcuts import redirect, render
from .services import oauth


def configuracion_correo(request):
    return render(request, "authentication/configuracion_correo.html")


def google_login(request):
    redirect_uri = request.build_absolute_uri("/auth/google/callback/")
    return oauth.google.authorize_redirect(request, redirect_uri)


def google_callback(request):
    token = oauth.google.authorize_access_token(request)

    print(token)

    return redirect("configuracion_correo")