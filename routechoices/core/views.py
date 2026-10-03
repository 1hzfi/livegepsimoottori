from pathlib import Path

from django.contrib.auth.decorators import login_not_required
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe

SECURITY_TXT_PATH = Path(__file__).parent / "security.txt"


@login_not_required
@require_safe
@cache_control(max_age=60 * 5, public=True)  # 5 minutes
def security_txt(request: HttpRequest) -> HttpResponse:
    """
    Serve the security.txt file, per:
    https://adamj.eu/tech/2026/10/01/django-security-txt/
    """
    return FileResponse(
        SECURITY_TXT_PATH.open("rb"),
        content_type="text/plain; charset=utf-8",
    )
