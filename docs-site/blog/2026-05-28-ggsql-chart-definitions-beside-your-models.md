---
slug: ggsql-chart-definitions-beside-your-models
title: GGSQL Chart Definitions Beside Your Models
description: Why Glyf keeps SQL-native chart grammar close to the dbt models it reads.
image: /img/examples/product-analytics-banner.svg
tags:
  - ggsql
  - charts
  - dbt
---

Chart definitions are easier to review when they live beside the models they query.
That is the reason Glyf supports GGSQL as a project-native visualization grammar.

<!-- truncate -->

Instead of configuring charts through a separate dashboard UI, a team can keep the chart SQL,
visualization directives, and labels in source control. The build then resolves dbt `ref()`
calls, validates the chart specs, and renders dashboard output as files.

The goal is a smaller gap between data modeling and visualization: the same repository, the
same review path, and the same deployment pipeline.
