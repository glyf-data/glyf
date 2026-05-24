import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

const layerBenefits = [
  ['Lineage bridge', 'Connect model metadata, chart SQL, and dashboard specs in one reviewable workflow.'],
  ['Versioned dashboard specs', 'Define layouts, filters, and charts in YAML beside analytical code.'],
  ['Static artifacts', 'Render dashboard assets for docs, CI, and lightweight publishing.'],
  ['Open workflow', 'Keep visualization definitions portable, inspectable, and extensible.'],
];

const featureLinks = [
  ['Quickstart', 'Run the included analytical project and render your first dashboard.', '/docs/get-started/quickstart'],
  ['Command reference', 'See every CLI command, option, and common workflow.', '/docs/reference/cli'],
  ['Technical guide', 'Understand parsing, dbt artifact resolution, rendering, and output paths.', '/docs/guides/technical-architecture'],
  ['GGSQL syntax', 'Write SQL-native visualizations with the supported ggsql directives.', '/docs/guides/visualisation-syntax'],
];

const examples = [
  ['Simple dbt', 'A compact revenue dashboard and chart syntax sampler.', '/docs/examples/simple-dbt'],
  ['Sales dashboard', 'Monthly revenue, channel mix, and regional sales.', '/docs/examples/sales-dashboard'],
  ['Product analytics', 'Active users, activation rate, and plan behavior.', '/docs/examples/product-analytics'],
  ['Finance metrics', 'Bookings, expense share, and gross margin signals.', '/docs/examples/finance-metrics'],
];

function HeroMock() {
  return (
    <div className="heroMock" aria-label="Glyf visualization and dashboard artifact preview">
      <div className="mockPanel mockPanel--code">
        <div className="mockPanel__topline">
          <span>Glyf + GGSQL</span>
          <span>revenue.ggsql</span>
        </div>
        <pre>{`from ref('fct_orders')
|> group by order_month
|> measure revenue = sum(revenue)
|> visualize line
     x: order_month
     y: revenue
     color: region`}</pre>
      </div>
      <div className="mockPanel mockPanel--chart">
        <div className="mockPanel__topline">
          <span>Revenue over time</span>
          <span>dashboard artifact</span>
        </div>
        <div className="lineChart" aria-hidden="true">
          <svg viewBox="0 0 360 170" role="img">
            <defs>
              <linearGradient id="chartLine" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0" stopColor="#0ea5e9" />
                <stop offset="1" stopColor="#00a870" />
              </linearGradient>
            </defs>
            <path d="M24 140 L72 120 L116 128 L158 84 L202 98 L248 58 L296 76 L336 36" fill="none" stroke="url(#chartLine)" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M24 140 L72 120 L116 128 L158 84 L202 98 L248 58 L296 76 L336 36 L336 154 L24 154 Z" fill="rgba(0,168,112,0.1)" />
            {[24, 72, 116, 158, 202, 248, 296, 336].map((x, index) => (
              <circle key={x} cx={x} cy={[140, 120, 128, 84, 98, 58, 76, 36][index]} r="5" fill="#ffffff" stroke="#00a870" strokeWidth="3" />
            ))}
          </svg>
        </div>
      </div>
      <div className="mockPanel mockPanel--donut">
        <div className="mockPanel__topline"><span>Region mix</span></div>
        <div className="donutVisual" aria-hidden="true"><span>$12.4M<br />Total</span></div>
        <ul className="miniLegend">
          <li><span /> US 48%</li>
          <li><span /> EMEA 30%</li>
          <li><span /> APAC 22%</li>
        </ul>
      </div>
      <div className="mockPanel mockPanel--bars">
        <div className="mockPanel__topline"><span>Top products</span></div>
        <div className="barRows" aria-hidden="true">
          <span style={{'--w': '94%'}} />
          <span style={{'--w': '78%'}} />
          <span style={{'--w': '61%'}} />
          <span style={{'--w': '46%'}} />
        </div>
      </div>
    </div>
  );
}

function HomepageHeader() {
  return (
    <header className="landingHero">
      <div className="container landingHero__layout">
        <div className="landingHero__content">
          <p className="eyebrow">SQL-native · open source · analytics engineering</p>
          <h1>A Semantic Visualization Layer for Analytical Systems</h1>
          <p className="landingHero__lead">
            Glyf connects analytical metadata, GGSQL visualizations, and dashboard specs so teams can trace insight from transformation to published artifact.
          </p>
          <div className="buttonRow">
            <Link className="button button--primary button--lg" to="/docs/get-started/quickstart">
              Get started
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/guides/visualisation-syntax">
              Explore GGSQL support
            </Link>
          </div>
          <div className="heroMeta" aria-label="Project qualities">
            <span>Open source</span>
            <span>Python CLI</span>
            <span>dbt artifact integration</span>
          </div>
        </div>
        <HeroMock />
      </div>
    </header>
  );
}

function AnalyticsLayers() {
  return (
    <section className="band band--layers">
      <div className="container layerBox">
        <div className="sectionHeader sectionHeader--center">
          <p className="eyebrow">Built for analytics engineers</p>
          <h2>Layered into the modern analytics workflow</h2>
          <p>
            Glyf sits in the visualization layer, downstream of transformation and quality checks, where analytical lineage often loses context.
          </p>
        </div>
        <div className="layerDiagram" aria-label="Transformation, quality, and visualization layers">
          <article className="layerCard layerCard--transform">
            <span className="layerLabel">Transformation</span>
            <strong>dbt</strong>
            <p>Models, refs, sources, lineage, and manifest artifacts.</p>
          </article>
          <span className="layerConnector" aria-hidden="true" />
          <article className="layerCard layerCard--quality">
            <span className="layerLabel">Data quality</span>
            <strong>dbt tests + observability framework</strong>
            <p>Assertions, freshness, checks, and operational confidence.</p>
          </article>
          <span className="layerConnector" aria-hidden="true" />
          <article className="layerCard layerCard--visualize">
            <span className="layerLabel">Visualization</span>
            <strong>Glyf</strong>
            <p>GGSQL charts, dashboard specs, and rendered dashboard artifacts.</p>
          </article>
        </div>
        <div className="benefitStrip">
          {layerBenefits.map(([title, description]) => (
            <div className="benefitItem" key={title}>
              <strong>{title}</strong>
              <span>{description}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function GgsqlSection() {
  return (
    <section className="band">
      <div className="container ggsqlLayout">
        <div>
          <p className="eyebrow">Glyf + GGSQL</p>
          <h2>GGSQL provides the SQL visualization grammar. Glyf brings it into an analytics-engineering workflow.</h2>
          <p>
            GGSQL is a separate open source project focused on SQL-native visualization. Glyf supports GGSQL today and adds the surrounding integration: dbt artifact resolution, dashboard specifications, validation commands, and rendered outputs.
          </p>
          <p>
            That boundary matters. Glyf does not pretend to own the visualization grammar. It gives GGSQL a practical path into analytical projects while leaving room for future visualization specs and user preferences.
          </p>
        </div>
        <div className="ggsqlBridge" aria-label="GGSQL and Glyf responsibilities">
          <article>
            <span>GGSQL</span>
            <h3>SQL visualization engine</h3>
            <ul>
              <li>SQL-native chart grammar</li>
              <li>Visualization primitives</li>
              <li>Query-oriented authoring</li>
            </ul>
          </article>
          <div className="bridgeMark" aria-hidden="true">+</div>
          <article>
            <span>Glyf</span>
            <h3>Integration and dashboard layer</h3>
            <ul>
              <li>dbt artifact integration</li>
              <li>Dashboard YAML specs</li>
              <li>Static artifacts for docs and CI</li>
            </ul>
          </article>
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
          <h2>Start with the docs you need</h2>
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
            Each example includes seeds, analytical models, GGSQL visualisations, dashboard YAML, and repeatable commands. Use them as starting points for your own analytics project.
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
          <p className="eyebrow">AI-assisted dashboard workflow</p>
          <h2>Give coding assistants the right project context</h2>
          <p>
            Point an assistant at the analytical project, manifest, chart files, and dashboard YAML, then ask it to draft `.ggsql`, update the dashboard, run validation, and report what still needs review.
          </p>
        </div>
        <div className="terminalPanel" aria-label="AI context command examples">
          <code>curl https://glyf.pages.dev/llms.txt</code>
          <code>uv run glyf doctor --project-dir examples/simple_dbt</code>
          <code>uv run glyf render --project-dir examples/simple_dbt</code>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout
      title="A Semantic Visualization Layer for Analytical Systems"
      description="Glyf connects analytical metadata, GGSQL visualizations, and dashboard specs for analytics engineering workflows."
    >
      <HomepageHeader />
      <main>
        <AnalyticsLayers />
        <GgsqlSection />
        <FeatureLinks />
        <Examples />
        <AgentSection />
      </main>
    </Layout>
  );
}
