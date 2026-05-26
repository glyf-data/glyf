import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

const featureCards = [
  ['dbt ref() in every chart', 'Use {{ ref() }} in chart SQL. Glyf reads the dbt manifest and validates queries before publish.'],
  ['Zero-server static output', 'Produce self-contained HTML and chart assets your team can host in docs, apps, storage, or CI.'],
  ['Generated React components', 'Compile dashboards to typed .tsx components for product analytics without an embedded BI SDK.'],
  ['Programmable Python macros', 'Reuse dashboard logic for thresholds, labels, and plan-based views in reviewed Python code.'],
  ['Visual diff as a build artifact', 'Compare dashboard builds and annotate metric shifts, new categories, and trend reversals.'],
  ['Pipeline hooks and alerts', 'Declare Slack or webhook alerts in dashboard YAML when metrics cross a threshold.'],
  ['Agent-ready MCP server', 'Expose the spec graph so agents can inspect model-to-chart impact and downstream breakage.'],
  ['Version controlled, reviewable', 'Keep chart definitions, layouts, and macros in Git with PR review and normal revert paths.'],
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

const problemItems = [
  ['Expensive BI platforms set the terms', 'Looker, Sigma, Tableau, and embedded analytics products make simple publishing a procurement problem. Glyf keeps the artifact as a file.'],
  ['Dashboards live outside the workflow', 'Your dbt models are in Git. Your charts are usually configured through a browser, stored elsewhere, and maintained by whoever last touched the UI.'],
  ['Columns rename. Charts break silently.', 'When dbt models change, dashboard failures often show up late. Glyf moves chart definitions into a build step that can validate earlier.'],
  ['Notebooks become one-off chart systems', 'When a BI platform cannot produce the shape of chart someone needs, the workaround often lives in a notebook and drifts from the pipeline.'],
  ['Embedded analytics should not require a vendor', 'For product dashboards and internal portals, rendered HTML and chart assets are often enough to publish where the audience already is.'],
  ['AI agents need a visualization artifact', 'Agents can inspect dbt models and draft SQL, but they still need a project-native way to render, validate, and publish the chart output.'],
];

const workflowSteps = [
  ['01 — Chart Definition', 'Write charts in GGSQL', 'SQL you already know, extended with a visualization grammar. Use ref() to reference dbt models directly.'],
  ['02 — Dashboard Layout', 'Compose in YAML + Python', 'Lay out charts into sections. Use Python macros for conditional logic, thresholds, and reusable components.'],
  ['03 — Build Output', 'Run one command', 'Glyf resolves dbt artifacts, validates chart specs, renders charts, and emits the files you can publish.'],
];

const personas = [
  ['Analytics Engineer', 'You work in dbt. Glyf is your next step.', 'You know SQL. You version-control everything. You should not need LookML or a BI platform UI to publish a declared dashboard artifact.'],
  ['Data Scientist', 'Charts in SQL, not one-off notebooks.', 'Write SQL-style chart definitions that run in the pipeline, stay current, and live beside the models they query.'],
  ['Data Leader', 'Reduce platform dependency.', 'Glyf is open source, runs locally, and produces outputs your team already knows how to deploy and review.'],
  ['Application Engineer', 'Import or publish a dashboard artifact.', 'The data team owns the spec. You consume rendered output or future components without negotiating with an embedded analytics vendor.'],
];

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

function WhyGlyfIcon({type}) {
  if (type === 'dbt') {
    return <DbtMark />;
  }

  if (type === 'ir') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3L20 7.5V16.5L12 21L4 16.5V7.5L12 3Z" />
        <path d="M4 7.5L12 12L20 7.5M12 12V21" />
      </svg>
    );
  }

  if (type === 'declarative') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 3H14L19 8V21H7V3Z" />
        <path d="M14 3V8H19" />
        <path d="M10 14H15M10 17H14" />
      </svg>
    );
  }

  if (type === 'agent') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 4V7M12 17V20M4 12H7M17 12H20" />
        <path d="M8.5 8.5H15.5V15.5H8.5V8.5Z" />
        <path d="M10.5 11H10.6M13.4 11H13.5M10.4 13.8H13.6" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 6L4 12L9 18" />
      <path d="M15 6L20 12L15 18" />
      <path d="M13 4L11 20" />
    </svg>
  );
}

function VectorIcon({type}) {
  if (type === 'publish') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 19H19" />
        <path d="M12 5V15" />
        <path d="M8 9L12 5L16 9" />
        <path d="M7 15H17" />
      </svg>
    );
  }

  if (type === 'diff') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 7H12" />
        <path d="M5 17H12" />
        <path d="M16 6L20 10L16 14" />
        <path d="M20 10H10" />
      </svg>
    );
  }

  if (type === 'component') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 8L4 12L8 16" />
        <path d="M16 8L20 12L16 16" />
        <path d="M14 5L10 19" />
      </svg>
    );
  }

  if (type === 'agent') {
    return <WhyGlyfIcon type="agent" />;
  }

  if (type === 'spark') {
    return <SparkleIcon />;
  }

  if (type === 'database') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <ellipse cx="12" cy="6" rx="6" ry="3" />
        <path d="M6 6V12C6 13.7 8.7 15 12 15C15.3 15 18 13.7 18 12V6" />
        <path d="M6 12V18C6 19.7 8.7 21 12 21C15.3 21 18 19.7 18 18V12" />
      </svg>
    );
  }

  if (type === 'notebook') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 4H18V20H7C5.9 20 5 19.1 5 18V6C5 4.9 5.9 4 7 4Z" />
        <path d="M9 8H15" />
        <path d="M9 12H16" />
        <path d="M9 16H13" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 4L20 8V16L12 20L4 16V8L12 4Z" />
      <path d="M4 8L12 12L20 8" />
      <path d="M12 12V20" />
    </svg>
  );
}

function HeroCodeWindow() {
  return (
    <div className="heroCodeVisual" aria-label="GGSQL chart definition compiled by glyf build">
      <div className="heroCodeWindow">
        <div className="heroCodeTitlebar">
          <span className="windowDot windowDot--red" />
          <span className="windowDot windowDot--yellow" />
          <span className="windowDot windowDot--green" />
          <strong>sessions_by_plan.ggsql</strong>
        </div>
        <pre className="heroCodeBody"><code><span className="codeKw">SELECT</span>{'\n'}
{'  '}plan,{'\n'}
{'  '}<span className="codeFn">sum</span>(sessions) <span className="codeKw">as</span> sessions{'\n'}
<span className="codeKw">FROM</span> <span className="codeRef">{'{{ ref(\'fct_product_usage\') }}'}</span>{'\n'}
<span className="codeKw">GROUP BY</span> 1{'\n\n'}
<span className="codeClause">VISUALISE</span> plan <span className="codeKw">AS</span> x, sessions <span className="codeKw">AS</span> y{'\n'}
<span className="codeClause">DRAW</span> pie{'\n'}
<span className="codeClause">LABEL</span> title <span className="codeOp">=&gt;</span> <span className="codeStr">'Sessions by Plan'</span>{'\n'}
<span className="codeClause">INTERACT</span> tooltip</code></pre>
        <div className="heroBuildCommand" aria-hidden="true">
          <span>↓</span>
          <strong>glyf build</strong>
          <span>↓</span>
        </div>
        <div className="heroBuildOutput">
          <p>Build output</p>
          <div>
            <span>product.html</span>
            <span>ProductDashboard.tsx</span>
            <span>chart.svg</span>
            <span>diff.html</span>
          </div>
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
          <p className="heroBadge"><SparkleIcon /> Open Source · CLI First · Lower the BI Cost</p>
          <h1>
            <span>Visualization</span>
            <em>belongs in</em>
            <span>the pipeline.</span>
          </h1>
          <p className="landingHero__lead">
            Glyf is the open-source build step for data visualization.
          </p>
          <div className="heroValueLine" aria-label="Glyf workflow summary">
            <span>Define Charts</span>
            <b aria-hidden="true">·</b>
            <span>Compose Dashboards</span>
            <b aria-hidden="true">·</b>
            <span>Publish Anywhere</span>
          </div>
          <div className="buttonRow">
            <Link className="heroPrimaryButton" to="/docs/get-started/quickstart">
              <span aria-hidden="true">&gt;_</span> Get Started <span aria-hidden="true">&rarr;</span>
            </Link>
            <Link className="heroGithubButton" to="/docs/examples/gallery">
              <SmallChartIcon type="bars" />
              Open Gallery
            </Link>
          </div>
        </div>
        <HeroCodeWindow />
      </div>
    </header>
  );
}

function ProblemSection() {
  return (
    <section className="problemSection">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">The problem</p>
          <h2>Your pipeline is complete.<br />Except the last mile.</h2>
          <p>
            Every stage of the modern data stack has declarative, version-controlled, testable
            artifacts. Every stage except visualization.
          </p>
        </div>
        <div className="problemGrid">
          {problemItems.map(([title, description], index) => (
            <article className="problemCard" key={title}>
              <div className="cardIcon">
                <VectorIcon type={['database', 'publish', 'diff', 'notebook', 'component', 'agent'][index]} />
              </div>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
        <div className="problemQuote">
          Your models are versioned. Your jobs are automated. Your data quality is tested.
          <strong> Visualization is still the last artifact outside the pipeline.</strong>
        </div>
        <div className="solutionDivider" aria-hidden="true">
          <span>Glyf</span>
        </div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  return (
    <section className="featuresSection">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">Features</p>
          <h2>What makes Glyf different.</h2>
        </div>
        <div className="featureStrip">
          {featureCards.map(([title, description]) => (
            <article className="featureStripItem" key={title}>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="howSection">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">How it works</p>
          <h2>Charts, dashboards, and outputs in one build step.</h2>
          <p>
            Glyf keeps authoring close to the project: chart grammar in GGSQL, dashboard composition
            in YAML, reusable logic in Python, and outputs from the CLI.
          </p>
        </div>
        <div className="howCodeGrid">
          <article className="howCodeStep">
            <span>{workflowSteps[0][0]}</span>
            <h3>{workflowSteps[0][1]}</h3>
            <p>{workflowSteps[0][2]}</p>
            <div className="miniCodeWindow">
              <div>sessions_by_plan.ggsql</div>
              <pre><code><span className="codeKw">SELECT</span> plan, <span className="codeFn">sum</span>(sessions){'\n'}
<span className="codeKw">FROM</span> <span className="codeRef">{'{{ ref(\'fct_usage\') }}'}</span>{'\n'}
<span className="codeKw">GROUP BY</span> 1{'\n\n'}
<span className="codeClause">VISUALISE</span> plan <span className="codeKw">AS</span> x{'\n'}
<span className="codeClause">DRAW</span> pie{'\n'}
<span className="codeClause">LABEL</span> title <span className="codeOp">=&gt;</span> <span className="codeStr">'Sessions'</span></code></pre>
            </div>
          </article>
          <article className="howCodeStep">
            <span>{workflowSteps[1][0]}</span>
            <h3>{workflowSteps[1][1]}</h3>
            <p>{workflowSteps[1][2]}</p>
            <div className="miniCodeWindow">
              <div>product.yml</div>
              <pre><code><span className="codeKw">sections</span>:{'\n'}
{'  '}- title: <span className="codeStr">Activation</span>{'\n'}
{'    '}items:{'\n'}
{'      '}- component:{'\n'}
{'          '}<span className="codeFn">{'{{ activation_health(0.82) }}'}</span>{'\n'}
{'      '}- chart: sessions_by_plan{'\n'}
{'      '}- chart: active_users</code></pre>
            </div>
          </article>
          <article className="howCodeStep">
            <span>{workflowSteps[2][0]}</span>
            <h3>{workflowSteps[2][1]}</h3>
            <p>{workflowSteps[2][2]}</p>
            <div className="miniCodeWindow">
              <div>Terminal</div>
              <pre><code><span className="codeFn">$</span> glyf build{'\n\n'}
<span className="codeMuted">✓ Resolved 6 ref() calls</span>{'\n'}
<span className="codeMuted">✓ Compiled 8 charts</span>{'\n'}
<span className="codeMuted">✓ Built product.html</span>{'\n'}
<span className="codeMuted">✓ Wrote chart assets</span>{'\n'}
<span className="codeFn">✓ Build complete in 2.1s</span></code></pre>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

function PersonasSection() {
  return (
    <section className="personasSection">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">Who it's for</p>
          <h2>Built for every role in the data team.</h2>
        </div>
        <div className="personasGrid">
          {personas.map(([role, title, description], index) => (
            <article className="personaCard" key={role}>
              <div className="cardIcon">
                <VectorIcon type={['database', 'notebook', 'publish', 'component'][index]} />
              </div>
              <span>{role}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
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
          <div className="ggsqlCopyBlocks">
            <div>
              <h2>GGSQL provides the SQL visualization grammar.</h2>
              <p>
                GGSQL is a separate open source project focused on SQL-native visualization:
                chart grammar, visualization primitives, and query-oriented authoring. Learn
                more at <a href="https://ggsql.org">ggsql.org</a>.
              </p>
            </div>
            <div>
              <h2>Glyf brings it into an analytics-engineering workflow.</h2>
              <p>
                Glyf supports GGSQL today and adds the surrounding project layer: dbt artifact
                resolution, dashboard YAML, validation commands, and rendered outputs your team
                can publish.
              </p>
            </div>
          </div>
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
              <li>Rendered artifacts for docs, apps, and CI</li>
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
    <section className="band examplesSection">
      <div className="container splitLayout">
        <div>
          <p className="eyebrow">Examples gallery</p>
          <h2>Open gallery of working examples</h2>
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

export default function Home() {
  return (
    <Layout
      title="Visualization belongs in the pipeline"
      description="Glyf is the open-source build step for dbt-aware visualization artifacts."
    >
      <HomepageHeader />
      <main>
        <ProblemSection />
        <HowItWorks />
        <FeaturesSection />
        <GgsqlSection />
        <PersonasSection />
        <FeatureLinks />
        <Examples />
      </main>
    </Layout>
  );
}
