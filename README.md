[![CircleCI](https://dl.circleci.com/status-badge/img/gh/routechoiceslivegps/livegepsimootori/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/routechoiceslivegps/livegepsimootori/tree/main) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/routechoiceslivegps/livegepsimootori/main.svg)](https://results.pre-commit.ci/latest/github/routechoiceslivegps/livegepsimootori/main) [![codecov](https://codecov.io/gh/routechoiceslivegps/livegepsimootori/graph/badge.svg?token=OZLCAY280V)](https://codecov.io/gh/routechoiceslivegps/livegepsimootori)

GPSTrackingServer
=================

Django application for serving a GPS Tracking SaaS platform

It delivers:
  - A static frontend for the SaaS: landing, pricing and help pages.
  - A listing of featured events hosted on the platform.
  - A separate listing of public events for each customer.
  - A web app for viewing events.
  - A dashboard for users to manage their clubs, events, maps, GPS tracking devices.
  - A documented REST API.
  - Multiple TCP servers listening to different GPS tracker protocols.
  - A WMS and a WMTS server for user uploaded maps and for proxying background map layers.
  - Multiple other map/gps related web tools.
  - An admin interface for the staff.

This project heavily relies on the Django, and on the Tornado Web, Python frameworks.

Hosted at https://www.routechoices.com
