from django.contrib.sitemaps import views as sitemaps_views
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django_hosts.resolvers import reverse

from routechoices.core import views as core_views
from routechoices.site import feeds, views
from routechoices.site.sitemaps import DynamicViewSitemap, StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "dynamic": DynamicViewSitemap,
}

urlpatterns = [
    path(
        "",
        include(
            (
                [
                    path("", views.landing_page, name="landing_page"),
                    re_path(
                        r"^live-gps-tracking/?$",
                        views.home_page,
                        name="landing_page_redirect",
                    ),
                    re_path(
                        r"^login/?$",
                        RedirectView.as_view(
                            url=reverse("account_login", host="dashboard")
                        ),
                        name="account_login",
                    ),
                    re_path(
                        r"^signup/?$",
                        RedirectView.as_view(
                            url=reverse("account_signup", host="dashboard")
                        ),
                        name="account_signup",
                    ),
                    re_path(
                        r"^events/?$", views.events_view, name="public_events_view"
                    ),
                    re_path(
                        r"^typo/(?P<typo>.*)",
                        TemplateView.as_view(template_name="site/typo.html"),
                        name="typo_view",
                    ),
                    re_path(
                        r"^feed(.rss)?$",
                        feeds.live_event_feed,
                        name="public_events_feed",
                    ),
                    re_path(
                        r"^trackers/?$",
                        TemplateView.as_view(template_name="site/tracker.html"),
                        name="trackers_view",
                    ),
                    re_path(
                        r"^guide/geojson/?$",
                        TemplateView.as_view(template_name="site/geojson.html"),
                        name="geojson_guide_view",
                    ),
                    re_path(
                        r"^privacy-policy/?$",
                        TemplateView.as_view(template_name="site/privacy_policy.html"),
                        name="privacy_policy_view",
                    ),
                    re_path(
                        r"^tos/?$",
                        TemplateView.as_view(template_name="site/tos.html"),
                        name="tos_view",
                    ),
                    re_path(
                        r"^pricing/?$",
                        views.pricing_page,
                        name="pricing_view",
                    ),
                    re_path(
                        r"^proceed-payment/?$",
                        views.pay_view,
                        name="pay_view",
                    ),
                    re_path(
                        r"(?P<icon_name>favicon\.ico|apple-touch-icon\.png|icon-192\.png|icon-512\.png)",
                        views.site_favicon,
                        name="site_favicon",
                    ),
                    path("robots.txt", views.robots_txt, name="robots.txt"),
                    path(
                        "llms.txt",
                        TemplateView.as_view(
                            template_name="llms.txt", content_type="text/plain"
                        ),
                        name="llms.txt",
                    ),
                    path(
                        "sitemap.xml",
                        sitemaps_views.sitemap,
                        {"sitemaps": sitemaps},
                        name="sitemap.xml",
                    ),
                ],
                "site",
            ),
            namespace="site",
        ),
    ),
    re_path(
        r"^(?P<club_slug>[0-9a-zA-Z][0-9a-zA-Z-]+)/(?P<path>.*)$",
        views.handle_alt_club_url,
        name="alt_club_url",
    ),
    path(".well-known/security.txt", core_views.security_txt),
]
