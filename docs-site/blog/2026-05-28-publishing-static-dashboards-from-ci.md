---
slug: publishing-static-dashboards-from-ci
title: Publishing Static Dashboards from CI
description: How static dashboard output fits into a normal analytics engineering release flow.
image: /img/examples/sales-dashboard-banner.svg
tags:
  - ci
  - deployment
  - dashboards
---

Dashboards do not need a running service to be useful. For many internal workflows, static
HTML and chart assets are enough.

<!-- truncate -->

Glyf is built around that deployment shape. A CI job can install dependencies, resolve dbt
artifacts, run `glyf build`, and publish the generated output to any static host.

That makes visualization part of the same release process as the rest of an analytics project:
review the change, build the artifact, and deploy the files.
