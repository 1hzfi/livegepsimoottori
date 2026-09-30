[![CircleCI](https://dl.circleci.com/status-badge/img/gh/routechoiceslivegps/livegepsimootori/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/routechoiceslivegps/livegepsimootori/tree/main) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/routechoiceslivegps/livegepsimootori/main.svg)](https://results.pre-commit.ci/latest/github/routechoiceslivegps/livegepsimootori/main) [![codecov](https://codecov.io/gh/routechoiceslivegps/livegepsimootori/graph/badge.svg?token=OZLCAY280V)](https://codecov.io/gh/routechoiceslivegps/livegepsimootori)

GPSTrackingServer
=================

Django application for serving a GPS Tracking SaaS platform

It contains code that deliver:
  - A static web frontend for a SaaS: landing, pricing, help, tos…
  - A web listing of featured events hosted on the platform.
  - A separate web listing of public events for each customer hosted on customizable domain name.
  - A web app for viewing events.
  - A dashboard for users to manage their clubs, events, maps, GPS tracking devices.
  - A documented public REST API.
  - TCP servers listening to different GPS tracking device protocols.
  - WMS/WMTS servers for user uploaded maps and for background maps layers.
  - Multiple other map/gps related web and cli tools.
  - An administration web interface for the staff.

This project heavily relies on the Django, and on the Tornado Web, Python frameworks.

See it in action at https://www.routechoices.com
