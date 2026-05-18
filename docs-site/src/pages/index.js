import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

const workflow = [
  ['Build dbt models', 'Run dbt seed, run, build, or compile so the manifest and warehouse tables are available.'],
  ['Write ggsql', 'Keep chart SQL next to the dbt project and map result columns to visual roles.'],
  ['Render charts', 'Generate compiled SQL plus SVG, PNG, and optional Vega-Lite JSON artifacts.'],
  ['Export a site', 'Publish the generated dashboard folder to any static host or CI artifact store.'],
];

const examples = [
  ['Simple dbt', 'A compact revenue dashboard and chart syntax sampler.', '/docs/examples/simple-dbt'],
  ['Sales dashboard', 'Monthly revenue, channel mix, and regional sales.', '/docs/examples/sales-dashboard'],
  ['Product analytics', 'Active users, activation rate, and plan behavior.', '/docs/examples/product-analytics'],
  ['Finance metrics', 'Bookings, expense share, and gross margin signals.', '/docs/examples/finance-metrics'],
];

const featureLinks = [
  ['Quickstart', 'Run the included dbt project and export your first static dashboard.', '/docs/get-started/quickstart'],
  ['Command reference', 'See every CLI command, option, and common workflow.', '/docs/reference/cli'],
  ['Technical guide', 'Understand parsing, dbt artifact resolution, rendering, and export paths.', '/docs/guides/technical-architecture'],
  ['AI context', 'Use the docs index and prompts as a starting point for coding agents.', '/docs/ai-context/overview'],
  ['Integrations', 'Connect dbt-charts to CI, static hosting, and future orchestration workflows.', '/docs/integrations/overview'],
  ['Migration placeholder', 'Track the future path for moving Looker dashboards into dbt-charts.', '/docs/migrations/looker'],
];

function HomepageHeader() {
  return (
    <header className="landingHero">
      <div className="container landingHero__layout">
        <div className="landingHero__content">
          <p className="eyebrow">dbt-native dashboarding</p>
          <h1>A lightweight dashboard layer for analytics engineers</h1>
          <p className="landingHero__lead">
            Built for dbt and powered by ggsql. Compile SQL visualisations into static dashboards, no BI server required.
          </p>
          <div className="buttonRow">
            <Link className="button button--primary button--lg" to="/docs/get-started/quickstart">
              Start with the quickstart
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/examples/gallery">
              Browse examples
            </Link>
          </div>
        </div>
        <div className="pipelineVisual" aria-label="dbt pipeline to chart-as-code dashboard">
          <div className="pipelineStage pipelineStage--dbt">
            <div className="stageHeader">
              <span className="stageBadge">dbt</span>
              <strong>Model pipeline</strong>
            </div>
            <code>models/fct_revenue.sql</code>
            <code>target/manifest.json</code>
          </div>
          <span className="pipelineArrow">-></span>
          <div className="pipelineStage pipelineStage--code">
            <div className="stageHeader">
              <span className="stageBadge">code</span>
              <strong>Charts as code</strong>
            </div>
            <code>visualisations/revenue.ggsql</code>
            <code>dashboards/executive.yml</code>
          </div>
          <span className="pipelineArrow">-></span>
          <div className="pipelineStage pipelineStage--dashboard">
            <div className="stageHeader">
              <span className="stageBadge">site</span>
              <strong>Static dashboard</strong>
            </div>
            <div className="dashboardPreview" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
            <p>No BI server required</p>
          </div>
        </div>
      </div>
    </header>
  );
}

function Workflow() {
  return (
    <section className="band">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">Developer workflow</p>
          <h2>From dbt model to publishable dashboard</h2>
        </div>
        <div className="workflowGrid">
          {workflow.map(([title, description], index) => (
            <article className="workflowStep" key={title}>
              <span>{index + 1}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeatureLinks() {
  return (
    <section className="band band--muted">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">Documentation</p>
          <h2>Find the right entry point quickly</h2>
        </div>
        <div className="linkGrid">
          {featureLinks.map(([title, description, to]) => (
            <Link className="docTile" to={to} key={title}>
              <h3>{title}</h3>
              <p>{description}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

function Examples() {
  return (
    <section className="band">
      <div className="container splitLayout">
        <div>
          <p className="eyebrow">Examples gallery</p>
          <h2>Use small projects as patterns</h2>
          <p>
            Each example includes seeds, dbt models, ggsql visualisations, dashboard YAML, and repeatable commands. Use them as starting points for your own analytics project.
          </p>
          <Link className="button button--primary" to="/docs/examples/gallery">
            Open gallery
          </Link>
        </div>
        <div className="exampleList">
          {examples.map(([title, description, to]) => (
            <Link className="exampleItem" to={to} key={title}>
              <strong>{title}</strong>
              <span>{description}</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

function AgentSection() {
  return (
    <section className="band band--ink">
      <div className="container agentLayout">
        <div>
          <p className="eyebrow">AI context and agents</p>
          <h2>Make the project easier for coding assistants to understand</h2>
          <p>
            The docs include an AI context section, an llms.txt placeholder, and a future skills placeholder for Codex, Claude, or other coding agents that can help users generate visualisations and dashboards from dbt models.
          </p>
        </div>
        <div className="terminalPanel" aria-label="AI context command examples">
          <code>curl https://dbtcharts.pages.dev/llms.txt</code>
          <code>uv run dbt-charts doctor --project-dir examples/simple_dbt</code>
          <code>uv run dbt-charts render --project-dir examples/simple_dbt</code>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout
      title="A lightweight dashboard layer for analytics engineers"
      description="dbt-charts documentation, examples, CLI reference, integrations, and AI context for analytics engineers."
    >
      <HomepageHeader />
      <main>
        <Workflow />
        <FeatureLinks />
        <Examples />
        <AgentSection />
      </main>
    </Layout>
  );
}
