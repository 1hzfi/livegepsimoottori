import oauth2_provider.views as oauth2_views
from django.conf import settings
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from health_check.views import HealthCheckView
from rest_framework import permissions

from routechoices.api import views
from routechoices.core import views as core_views

schema_view = get_schema_view(
    openapi.Info(
        title="Routechoices.com - GPS Tracking - API",
        default_version="v1",
        description="Routechoices.com - GPS Tracking - API",
        terms_of_service="https://www.routechoices.com/tos/",
        contact=openapi.Contact(email="info@routechoices.com"),
        license=openapi.License(
            name="GPLv3", url="https://www.gnu.org/licenses/gpl-3.0.en.html"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url=f"https://api.{settings.PARENT_HOST}",
    urlconf="routechoices.api.urls",
)
ApiAuthorizationView = oauth2_views.AuthorizationView
ApiAuthorizationView.login_url = f"//api.{settings.PARENT_HOST}/login/"

oauth2_endpoint_views = [
    path("authorize/", oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path("token/", oauth2_views.TokenView.as_view(), name="token"),
    path("revoke-token/", oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]

urlpatterns = [
    re_path(r"^$", schema_view.with_ui("swagger", cache_timeout=60), name="api_doc"),
    re_path(r"^check-latlon/?$", views.ip_latlon, name="ip_latlon"),
    re_path(r"^event-set/$", views.event_set_creation, name="event_set"),
    path(
        r"healthcheck/",
        HealthCheckView.as_view(
            checks=[  # optional, default is all but 3rd party checks
                "health_check.Cache",
                "health_check.Database",
                "health_check.Mail",
                "health_check.Storage",
                # 3rd party checks
                "health_check.contrib.psutil.Disk",
                "health_check.contrib.psutil.Memory",
            ],
        ),
    ),
    path(
        "login/",
        views.CustomApiLoginView.as_view(),
        name="api_login",
    ),
    path(
        "mfa/",
        include("kagi.urls", namespace="kagi"),
    ),
    re_path(r"^locations/?$", views.locations_api_gw, name="locations_api_gw"),
    re_path(r"^time/?$", views.get_time, name="time_api"),
    re_path(r"^user/?$", views.user_view, name="user_view_api"),
    re_path(r"^version/?$", views.get_version, name="version"),
    path(
        "search/",
        include(
            [
                path("device", views.device_search, name="device_search_api"),
            ]
        ),
    ),
    path(
        "device/",
        include(
            [
                path("", views.create_device_id, name="device_api"),
                re_path(
                    r"^(?P<device_id>[^/]+)/",
                    include(
                        [
                            path(
                                "registrations",
                                views.device_registrations,
                                name="device_registrations_api",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "clubs/",
        include(
            [
                path(
                    "",
                    views.club_list_view,
                    name="club_list",
                )
            ]
        ),
    ),
    path(
        "events/",
        include(
            [
                path("", views.event_list, name="event_list"),
                re_path(
                    r"^(?P<event_id>[0-9a-zA-Z_-]+)/",
                    include(
                        [
                            path(
                                "",
                                views.event_detail,
                                name="event_detail",
                            ),
                            path(
                                "geojson",
                                views.event_geojson_download,
                                name="event_geojson_download",
                            ),
                            path(
                                "zip",
                                views.event_zip,
                                name="event_zip",
                            ),
                            path(
                                "data/",
                                include(
                                    [
                                        path(
                                            "",
                                            views.event_data,
                                            name="event_data",
                                        ),
                                        re_path(
                                            r"^(?P<previous_key>\d+)$",
                                            views.event_data_delta,
                                            name="event_data_delta",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "maps/",
                                include(
                                    [
                                        path(
                                            "",
                                            views.event_map_list,
                                            name="event_map_list",
                                        ),
                                        re_path(
                                            r"^(?P<index>[1-9]\d*)",
                                            include(
                                                [
                                                    path(
                                                        "/",
                                                        views.event_map_detail,
                                                        name="event_map_detail",
                                                    ),
                                                    re_path(
                                                        r"^\.(?P<extension>png|webp|avif|jpeg|kmz)$",
                                                        views.event_map_download,
                                                        name="event_map_download_with_format",
                                                    ),
                                                ]
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "competitors/",
        include(
            [
                path(
                    "",
                    views.create_competitor,
                    name="competitor_creation_view",
                ),
                re_path(
                    r"^(?P<competitor_id>[0-9a-zA-Z_-]+)/",
                    include(
                        [
                            path(
                                "",
                                views.competitor_api,
                                name="competitor_api",
                            ),
                            path(
                                "route",
                                views.competitor_route_upload,
                                name="competitor_route_upload",
                            ),
                            path(
                                "gpx",
                                views.competitor_gpx_download,
                                name="competitor_gpx_download",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "woo/race_status/",
        include(
            [
                path(
                    "get_info.json",
                    views.two_d_rerun_race_status,
                    name="2d_rerun_race_status",
                ),
                path(
                    "get_data.json",
                    views.two_d_rerun_race_data,
                    name="2d_rerun_race_data",
                ),
            ]
        ),
    ),
    path(
        "webhooks/",
        include(("routechoices.webhooks.urls", "webhooks"), namespace="webhooks"),
    ),
    path(
        "oauth2/",
        include(
            (oauth2_endpoint_views, "oauth2_provider"), namespace="oauth2_provider"
        ),
    ),
    path(".well-known/security.txt", core_views.security_txt),
]
