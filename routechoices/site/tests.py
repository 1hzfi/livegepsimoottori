import datetime as dt

import arrow
from allauth.account.models import EmailAddress
from django.core import mail
from rest_framework import status

from routechoices.api.tests import EssentialApiBase
from routechoices.core.models import Club, Event, EventSet
from routechoices.testing import APIClient


class SiteViewsTestCase(EssentialApiBase):
    def setUp(self):
        super().setUp()
        self.club = Club.objects.create(
            name="Kemiön Kiilat", slug="kiilat", upgraded=True
        )
        self.club.admins.set([self.user])

    def test_events_page_loads(self):
        s = EventSet.objects.create(
            club=self.club,
            name="Killa Cup",
        )
        Event.objects.create(
            name="Kiila Cup 1",
            slug="kiila-cup-1",
            club=self.club,
            featured=True,
            start_date=arrow.now().shift(days=-112).datetime,
            end_date=arrow.now().shift(days=-111).datetime,
            event_set=s,
        )
        Event.objects.create(
            name="Kiila Cup 2",
            slug="kiila-cup-2",
            club=self.club,
            featured=True,
            start_date=arrow.now().shift(minutes=-2).datetime,
            end_date=arrow.now().shift(minutes=-1).datetime,
            event_set=s,
        )
        Event.objects.create(
            name="Training",
            slug="training-1",
            club=self.club,
            featured=True,
            start_date=arrow.now().shift(hours=-2).datetime,
            end_date=arrow.now().shift(hours=-1).datetime,
        )

        client = APIClient(HTTP_HOST="www.rtchs.localhost")

        url = self.reverse_and_check("site:public_events_view", "/events", host="www")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = client.get(f"{url}?q=Kiila+Cup+2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, "Kiila Cup 1")
        self.assertContains(response, "Kiila Cup 2")
        response = client.get(f'{url}?q="Cup+2"')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, "Kiila Cup 1")
        self.assertContains(response, "Kiila Cup 2")
        response = client.get(
            f"{url}?year={arrow.get().shift(minutes=-1).year}&month={arrow.get().shift(minutes=-1).month}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, "Kiila Cup 1")
        self.assertContains(response, "Kiila Cup 2")

        url = self.reverse_and_check("site:public_events_feed", "/feed", host="www")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_semi_static_pages_loads(self):
        client = APIClient(HTTP_HOST="www.rtchs.localhost")
        url = self.reverse_and_check("site:landing_page", "/", host="www")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get("/favicon.ico")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get("/robots.txt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = self.reverse_and_check("site:trackers_view", "/trackers", host="www")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = self.reverse_and_check("site:pricing_view", "/pricing", host="www")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get("/sitemap.xml")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_send_message(self):
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, primary=True, verified=True
        )
        client = APIClient(HTTP_HOST="dashboard.rtchs.localhost")
        client.force_login(self.user)
        url = self.reverse_and_check("contact_view", "/contact/", host="dashboard")
        response = client.post(
            url, {"subject": "Hello, can I ask a question?", "message": "Does it work?"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue("Hello, can I ask a question?" in mail.outbox[0].subject)
        self.assertTrue(self.user.email in mail.outbox[0].subject)
        self.assertTrue(mail.outbox[0].body.startswith("Does it work?"))


class SecurityTxtTests(EssentialApiBase):
    """
    Test the security.txt file, per:
    https://adamj.eu/tech/2026/10/01/django-security-txt/
    """

    def test_success(self):
        self.client.defaults["HTTP_HOST"] = "www.rtchs.localhost"
        response = self.client.get(
            "https://www.rtchs.localhost/.well-known/security.txt", scheme="https"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["content-type"] == "text/plain; charset=utf-8"
        assert response["cache-control"] == "max-age=300, public"

        # Parse the security.txt format
        content = response.getvalue().decode()
        fields: dict[str, list[str]] = {}
        for line in content.splitlines():
            name, sep, value = line.partition(": ")
            if sep and not line.startswith("#"):
                fields.setdefault(name, []).append(value)

        assert fields["Contact"] == ["mailto:security@onehertz.fi"]
        assert len(fields["Expires"]) == 1
        expires = dt.datetime.fromisoformat(fields["Expires"][0])
        assert expires.tzinfo is not None

    def test_head(self):
        self.client.defaults["HTTP_HOST"] = "www.rtchs.localhost"
        response = self.client.head(
            "https://www.rtchs.localhost/.well-known/security.txt", scheme="https"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_post_disallowed(self):
        self.client.defaults["HTTP_HOST"] = "www.rtchs.localhost"
        response = self.client.post(
            "https://www.rtchs.localhost/.well-known/security.txt", scheme="https"
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
