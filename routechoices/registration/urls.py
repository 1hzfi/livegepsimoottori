from django.urls import path, re_path

from routechoices.core import views as core_views
from routechoices.site import views

urlpatterns = [
    re_path(
        r"^$",
        views.registration_view,
        name="registration_view",
    ),
    path(".well-known/security.txt", core_views.security_txt),
]
