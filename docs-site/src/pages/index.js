import React from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
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

function DbIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <ellipse cx="12" cy="6" rx="6.2" ry="3.1" />
      <path d="M5.8 6V12C5.8 13.7 8.6 15.1 12 15.1C15.4 15.1 18.2 13.7 18.2 12V6" />
      <path d="M5.8 12V18C5.8 19.7 8.6 21.1 12 21.1C15.4 21.1 18.2 19.7 18.2 18V12" />
    </svg>
  );
}

function DbtMark() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M12 10L24 18L36 10L40 14L32 24L40 34L36 38L24 30L12 38L8 34L16 24L8 14L12 10Z" />
    </svg>
  );
}

function SmallChartIcon({type}) {
  if (type === 'bars') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 18V12M12 18V8M19 18V5" />
      </svg>
    );
  }

  if (type === 'line') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 17L9 12L13 14L20 7" />
        <path d="M4 20H20" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 4V12H20" />
      <circle cx="12" cy="12" r="8" />
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3L14.3 9.7L21 12L14.3 14.3L12 21L9.7 14.3L3 12L9.7 9.7L12 3Z" />
    </svg>
  );
}

function HeroTraitIcon({type}) {
  if (type === 'dbt') {
    return <DbtMark />;
  }

  if (type === 'yaml') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 3H14L19 8V21H7V3Z" />
        <path d="M14 3V8H19" />
        <path d="M10 14H15M10 17H14" />
      </svg>
    );
  }

  if (type === 'license') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3L19 6V11C19 15.6 16.1 19.8 12 21C7.9 19.8 5 15.6 5 11V6L12 3Z" />
        <path d="M9 12L11.2 14.2L15.5 9.8" />
      </svg>
    );
  }

  return <DbIcon />;
}

function PipelineArrow() {
  return (
    <svg className="heroPipelineArrow" viewBox="0 0 52 32" aria-hidden="true">
      <path d="M4 16H45" />
      <path d="M33 5L45 16L33 27" />
    </svg>
  );
}

function HeroPipeline() {
  const logoUrl = useBaseUrl('/img/glyf-mark.svg');

  return (
    <div className="heroPipeline" aria-label="Analytics workflow from data ingestion to Glyf visualization">
      <article className="heroStage heroStage--ingest">
        <div className="stageIcon stageIcon--database"><DbIcon /></div>
        <h2>Data<br />Ingestion</h2>
        <span className="stageRule" />
        <p>Sources, APIs,<br />files, streams</p>
      </article>
      <PipelineArrow />
      <article className="heroStage heroStage--transform">
        <div className="dbtLogo"><DbtMark /><strong>dbt</strong></div>
        <h2>Transform<br />Data</h2>
        <span className="stageRule" />
        <p>dbt models<br />(CTEs, SQL)</p>
      </article>
      <PipelineArrow />
      <article className="heroStage heroStage--glyf">
        <span className="heroSpark"><SparkleIcon /></span>
        <div className="glyfStageBrand">
          <img src={logoUrl} alt="" />
          <strong>Glyf</strong>
        </div>
        <h2>Visualize with<br />SQL-style specs<br />&amp; dashboards</h2>
        <span className="glyfRule" />
        <div className="glyfStageIcons" aria-hidden="true">
          <span><SmallChartIcon type="bars" /></span>
          <span><SmallChartIcon type="line" /></span>
          <span><SmallChartIcon type="pie" /></span>
        </div>
      </article>
      <div className="heroLineage" aria-hidden="true">
        <span>End-to-end analytics lineage</span>
      </div>
    </div>
  );
}

function HomepageHeader() {
  return (
    <header className="landingHero">
      <div className="container landingHero__layout">
        <div className="landingHero__content">
          <p className="heroBadge"><SparkleIcon /> Open Source</p>
          <h1>Glyf &mdash; A Semantic Visualization Layer for Analytical Systems</h1>
          <p className="landingHero__lead">
            Write visualizations close to your data using SQL-style specs.
            Integrates with dbt, compiles to a portable IR, and renders charts and dashboards everywhere.
          </p>
          <div className="buttonRow">
            <Link className="heroPrimaryButton" to="/docs/get-started/quickstart">
              <span aria-hidden="true">&gt;_</span> Get Started <span aria-hidden="true">&rarr;</span>
            </Link>
            <Link className="heroGithubButton" to="https://github.com/kannandreams/glyf">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path fill="currentColor" d="M12 .5A11.5 11.5 0 0 0 .5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2.02c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.19-3.08-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18a10.95 10.95 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.11 3.04.74.8 1.19 1.82 1.19 3.08 0 4.42-2.69 5.39-5.25 5.68.41.35.78 1.05.78 2.12v3.14c0 .31.21.68.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5Z" />
              </svg>
              View on GitHub
            </Link>
          </div>
          <div className="heroMeta" aria-label="Project qualities">
            <span><HeroTraitIcon /> SQL-Native</span>
            <span><HeroTraitIcon type="dbt" /> dbt Integration</span>
            <span><HeroTraitIcon type="yaml" /> YAML Specs</span>
            <span><HeroTraitIcon type="license" /> Apache 2.0</span>
          </div>
        </div>
        <HeroPipeline />
        <div className="heroCommunityNote">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8.5 11.5C10.4 11.5 12 9.9 12 8S10.4 4.5 8.5 4.5S5 6.1 5 8S6.6 11.5 8.5 11.5Z" />
            <path d="M15.8 11C17.3 11 18.5 9.8 18.5 8.3S17.3 5.6 15.8 5.6" />
            <path d="M3.5 19C3.9 15.8 5.7 14.2 8.5 14.2C11.3 14.2 13.1 15.8 13.5 19" />
            <path d="M14.4 14.5C17.5 14.7 19.4 16.2 20 19" />
          </svg>
          <strong>Built by the community</strong>
          <i aria-hidden="true">&middot;</i>
          <strong>Apache 2.0 License</strong>
        </div>
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
