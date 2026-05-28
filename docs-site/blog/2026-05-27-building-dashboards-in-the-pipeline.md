---
slug: building-dashboards-in-the-pipeline
title: Building Dashboards in the Pipeline
description: A short note on why Glyf keeps dashboard definitions close to dbt models and CI.
image: /img/examples/simple-dbt-banner.svg
tags:
  - analytics engineering
  - dbt
  - dashboards
---

Most analytics projects already treat models, tests, and deployment scripts as source code.
Dashboards should be able to follow the same path.

<!-- truncate -->

Glyf starts from that idea. A chart definition can live beside the dbt project, refer to
models through `ref()`, and produce static output during a build. That keeps visualization
changes visible in review and makes generated dashboards easier to publish from CI.

This blog space will collect product notes, workflow examples, and practical guidance for
using Glyf in real analytics projects.
