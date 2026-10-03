from django.urls import path, re_path

from routechoices.core import views as core_views
from routechoices.wms import views

urlpatterns = [
    re_path(r"^/?$", views.wms_service, name="wms_service"),
    path(".well-known/security.txt", core_views.security_txt),
]
