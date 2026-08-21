from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .services import oauth


def login_view(request):
    # Si ya inició sesión, no tiene sentido mostrarle el formulario de nuevo.
    if request.user.is_authenticated:
        return redirect("applus")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        usuario = authenticate(request, username=username, password=password)

        if usuario is not None:
            login(request, usuario)
            siguiente = request.GET.get("next") or "applus"
            return redirect(siguiente)
        else:
            error = "Usuario o contraseña incorrectos."

    return render(request, "authentication/login.html", {"error": error})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


def configuracion_correo(request):
    return render(request, "authentication/configuracion_correo.html")


def google_login(request):
    redirect_uri = request.build_absolute_uri("/auth/google/callback/")
    return oauth.google.authorize_redirect(request, redirect_uri)


def google_callback(request):
    token = oauth.google.authorize_access_token(request)

    print(token)

    return redirect("configuracion_correo")