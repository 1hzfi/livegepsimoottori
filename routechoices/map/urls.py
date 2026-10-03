from django.urls import path, re_path
from django.views.generic import TemplateView

from routechoices.core import views as core_views

urlpatterns = [
    re_path(r"^$", TemplateView.as_view(template_name="site/map.html"), name="map"),
    path(".well-known/security.txt", core_views.security_txt),
]
