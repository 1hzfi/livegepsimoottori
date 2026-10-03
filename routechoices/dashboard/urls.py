from allauth.account import views as allauth_views
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from user_sessions import views as user_sessions_views

from routechoices.api import views as api_views
from routechoices.core import views as core_views
from routechoices.dashboard import views
from routechoices.site import views as site_views

admin.site.site_header = "Admin"
admin.site.site_title = "Admin Site"
admin.site.index_title = "Welcome to the administration site"
admin.site.site_url = f"//www.{settings.PARENT_HOST}"


urlpatterns = [
    path("", views.home_view, name="home_view"),
    path("admin/hijack/", include("hijack.urls")),
    path(
        "admin/login/",
        site_views.CustomAdminLoginView.as_view(),
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "go/",
        views.quick_event,
        name="quick_start_view",
    ),
    path(
        "starting-gate/",
        views.quick_event_share,
        name="quick_event_share",
    ),
    path("contact/", site_views.contact, name="contact_view"),
    path(
        "participations",
        views.participations_view,
        name="dashboard_participations_view",
    ),
    re_path(
        r"^contribute/(?P<club_slug>[a-zA-Z0-9][a-zA-Z0-9-]+)/(?P<slug>[a-zA-Z0-9][a-zA-Z0-9_-]+)/?$",
        views.event_contribute_view,
        name="event_contribute_view",
    ),
    path(
        "request-invite",
        views.club_request_invite_view,
        name="dashboard_request_club_invite_view",
    ),
    path(
        "account/",
        include(
            [
                path("", views.account_edit_view, name="account_edit_view"),
                path("emails", views.email_view, name="account_email_list"),
                path(
                    "change-password",
                    allauth_views.password_change,
                    name="account_password_change_view",
                ),
                path("delete", views.account_delete_view, name="account_delete_view"),
                path(
                    "sessions/",
                    include(
                        (
                            [
                                path(
                                    "",
                                    view=user_sessions_views.SessionListView.as_view(),
                                    name="list_view",
                                ),
                                path(
                                    "delete-others",
                                    view=views.CustomSessionDeleteOtherView.as_view(),
                                    name="delete_other_view",
                                ),
                            ],
                            "dashboard_account_session",
                        ),
                        namespace="account_session",
                    ),
                ),
                path("login/", RedirectView.as_view(url="/login")),
                path("logout/", RedirectView.as_view(url="/logout")),
                path("signup/", RedirectView.as_view(url="/signup")),
                path("email/", RedirectView.as_view(url="/account/emails")),
                path(
                    "password/change/",
                    RedirectView.as_view(url="/account/change-password"),
                ),
                path("", include("allauth.urls")),
            ],
        ),
    ),
    path(
        "account/mfa/",
        include(
            [
                path("login/", site_views.CustomLoginView.as_view()),
                path("backup-codes/", views.backup_codes, name="backup-codes"),
                path("", include("kagi.urls", namespace="kagi")),
            ]
        ),
    ),
    path(
        "clubs/",
        include(
            (
                [
                    path("", views.club_select_view, name="select_view"),
                    path("new", views.club_create_view, name="create_view"),
                    re_path(
                        r"^(?P<club_slug>[A-Za-z0-9_-]+)/",
                        include(
                            [
                                path(
                                    "",
                                    views.club_view,
                                    name="edit_view",
                                ),
                                path(
                                    "custom-domain",
                                    views.club_custom_domain_view,
                                    name="custom_domain_view",
                                ),
                                path(
                                    "delete",
                                    views.club_delete_view,
                                    name="delete_view",
                                ),
                                path(
                                    "send-invite",
                                    views.club_invite_add_view,
                                    name="send_invite_view",
                                ),
                                path("upgrade", views.upgrade, name="upgrade_view"),
                                path(
                                    "devices/",
                                    include(
                                        (
                                            [
                                                path(
                                                    "",
                                                    views.device_list_view,
                                                    name="list_view",
                                                ),
                                                path(
                                                    "csv",
                                                    views.device_list_download,
                                                    name="list_download",
                                                ),
                                                path(
                                                    "new",
                                                    views.device_add_view,
                                                    name="add_view",
                                                ),
                                                re_path(
                                                    r"^(?P<device_id>[^/]+)/",
                                                    include(
                                                        [
                                                            path(
                                                                "",
                                                                views.device_edit_view,
                                                                name="edit_view",
                                                            ),
                                                            path(
                                                                "delete",
                                                                views.device_delete_view,
                                                                name="delete_view",
                                                            ),
                                                        ]
                                                    ),
                                                ),
                                            ],
                                            "dashboard_club_device",
                                        ),
                                        namespace="device",
                                    ),
                                ),
                                path(
                                    "maps/",
                                    include(
                                        (
                                            [
                                                path(
                                                    "",
                                                    views.map_list_view,
                                                    name="list_view",
                                                ),
                                                path(
                                                    "new",
                                                    views.map_create_view,
                                                    name="create_view",
                                                ),
                                                path(
                                                    "draw",
                                                    views.map_draw_view,
                                                    name="draw_view",
                                                ),
                                                path(
                                                    "upload-gpx",
                                                    views.map_gpx_upload_view,
                                                    name="upload_gpx_view",
                                                ),
                                                path(
                                                    "merge",
                                                    views.merge_maps,
                                                    name="merge_maps_view",
                                                ),
                                                re_path(
                                                    r"(?P<map_id>[A-Za-z0-9_-]+)/",
                                                    include(
                                                        [
                                                            path(
                                                                "",
                                                                views.map_edit_view,
                                                                name="edit_view",
                                                            ),
                                                            path(
                                                                "delete",
                                                                views.map_delete_view,
                                                                name="delete_view",
                                                            ),
                                                        ]
                                                    ),
                                                ),
                                            ],
                                            "dashboard_club_map",
                                        ),
                                        namespace="map",
                                    ),
                                ),
                                path(
                                    "events/",
                                    include(
                                        (
                                            [
                                                path(
                                                    "",
                                                    views.event_list_view,
                                                    name="list_view",
                                                ),
                                                path(
                                                    "new",
                                                    views.event_create_view,
                                                    name="create_view",
                                                ),
                                                re_path(
                                                    r"^(?P<event_id>[A-Za-z0-9_-]+)/",
                                                    include(
                                                        [
                                                            path(
                                                                "",
                                                                views.event_edit_view,
                                                                name="edit_view",
                                                            ),
                                                            path(
                                                                "map",
                                                                views.event_map_edit_view,
                                                                name="map_edit_view",
                                                            ),
                                                            path(
                                                                "view",
                                                                views.private_view,
                                                                name="private_view",
                                                            ),
                                                            path(
                                                                "competitors",
                                                                views.event_competitors_view,
                                                                name="competitors_view",
                                                            ),
                                                            path(
                                                                "competitors.csv",
                                                                views.event_competitors_csv_view,
                                                                name="competitors_csv_view",
                                                            ),
                                                            path(
                                                                "competitors-printer-friendly",
                                                                views.event_competitors_printer_view,
                                                                name="competitors_printer_view",
                                                            ),
                                                            path(
                                                                "delete",
                                                                views.event_delete_view,
                                                                name="delete_view",
                                                            ),
                                                            path(
                                                                "route-upload",
                                                                views.event_route_upload_view,
                                                                name="route_upload_view",
                                                            ),
                                                        ]
                                                    ),
                                                ),
                                            ],
                                            "dashboard_club_event",
                                        ),
                                        namespace="event",
                                    ),
                                ),
                                path(
                                    "bundles/",
                                    include(
                                        (
                                            [
                                                path(
                                                    "",
                                                    views.event_set_list_view,
                                                    name="list_view",
                                                ),
                                                path(
                                                    "new",
                                                    views.event_set_create_view,
                                                    name="create_view",
                                                ),
                                                re_path(
                                                    r"(?P<event_set_id>[A-Za-z0-9_-]+)/",
                                                    include(
                                                        [
                                                            path(
                                                                "",
                                                                views.event_set_edit_view,
                                                                name="edit_view",
                                                            ),
                                                            path(
                                                                "delete",
                                                                views.event_set_delete_view,
                                                                name="delete_view",
                                                            ),
                                                        ]
                                                    ),
                                                ),
                                            ],
                                            "dashboard_club_event_set",
                                        ),
                                        namespace="event_set",
                                    ),
                                ),
                            ]
                        ),
                    ),
                ],
                "dashboard_club",
            ),
            namespace="dashboard_club",
        ),
    ),
    path(
        "competitors/",
        include(
            [
                path(
                    "",
                    api_views.create_competitor,
                    name="competitor_creation_view",
                ),
                re_path(
                    r"^(?P<competitor_id>[0-9a-zA-Z_-]+)/",
                    include(
                        [
                            path(
                                "",
                                api_views.competitor_api,
                                name="competitor_api",
                            ),
                            path(
                                "route",
                                api_views.competitor_route_upload,
                                name="competitor_route_upload",
                            ),
                            path(
                                "gpx",
                                api_views.competitor_gpx_download,
                                name="competitor_gpx_download",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "media/",
        include(
            (
                [
                    re_path(
                        r"^maps/(?P<map_id>[-0-9a-zA-Z_]{11})$",
                        views.dashboard_map_download,
                        name="map_download",
                    ),
                    re_path(
                        r"^maps/(?P<map_id>[-0-9a-zA-Z_]{11}).kmz$",
                        views.dashboard_map_download_as_kmz,
                        name="map_download",
                    ),
                    re_path(
                        r"^logos/(?P<club_id>[-0-9a-zA-Z_]{11})$",
                        views.dashboard_logo_download,
                        name="logo_download",
                    ),
                    re_path(
                        r"^banners/(?P<club_id>[-0-9a-zA-Z_]{11})$",
                        views.dashboard_banner_download,
                        name="banner_download",
                    ),
                    re_path(
                        r"^geojson/(?P<event_id>[-0-9a-zA-Z_]{11})$",
                        views.dashboard_geojson_download,
                        name="geojson_download",
                    ),
                ],
                "dashboard_media",
            ),
            namespace="dashboard_media",
        ),
    ),
    path("invitations/", include("invitations.urls", namespace="invitations")),
    path("hijack/release/", views.MyReleaseUserView.as_view(), name="hijack_release"),
    path("login", site_views.CustomLoginView.as_view(), name="account_login"),
    path("logout", allauth_views.logout, name="account_logout"),
    path("signup", site_views.CustomSignupView.as_view(), name="account_signup"),
    path("map", TemplateView.as_view(template_name="site/map.html"), name="map"),
    path(
        ".well-known/change-password",
        RedirectView.as_view(pattern_name="account_password_change_view"),
    ),
    path(".well-known/security.txt", core_views.security_txt),
]
