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

const outputSurfaces = [
  ['dashboard', 'Dashboard'],
  ['charts', 'Charts'],
  ['publish', 'Publish'],
  ['embed', 'Embed'],
];

function OutputIcon({type}) {
  if (type === 'dashboard') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="4" width="18" height="16" rx="2.5" />
        <path d="M7 15V11M12 15V8M17 15V12" />
      </svg>
    );
  }

  if (type === 'charts') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 18L9 12.5L13 15.5L20 7" />
        <path d="M4 20H20" />
        <circle cx="9" cy="12.5" r="1.4" />
        <circle cx="13" cy="15.5" r="1.4" />
        <circle cx="20" cy="7" r="1.4" />
      </svg>
    );
  }

  if (type === 'publish') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 16V4" />
        <path d="M8 8L12 4L16 8" />
        <path d="M5 14V18C5 19.1 5.9 20 7 20H17C18.1 20 19 19.1 19 18V14" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 8L5 12L9 16" />
      <path d="M15 8L19 12L15 16" />
      <path d="M13 5L11 19" />
    </svg>
  );
}

function HeroMock() {
  return (
    <div className="heroVisual" aria-label="Glyf visualization and dashboard artifact preview">
      <div className="heroMock">
        <div className="mockPanel mockPanel--code">
          <div className="mockPanel__topline">
            <span>‹</span>
            <strong>Glyf SQL (ggsql)</strong>
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
            <strong>Revenue over time</strong>
          </div>
          <div className="lineChart" aria-hidden="true">
            <svg viewBox="0 0 430 250" role="img">
              <g stroke="#e8edf3" strokeWidth="1">
                <path d="M58 38H392" />
                <path d="M58 82H392" />
                <path d="M58 126H392" />
                <path d="M58 170H392" />
                <path d="M58 214H392" />
              </g>
              <g fill="#42526b" fontSize="14" fontWeight="700">
                <text x="18" y="43">4M</text>
                <text x="18" y="87">3M</text>
                <text x="18" y="131">2M</text>
                <text x="18" y="175">1M</text>
                <text x="30" y="219">0</text>
              </g>
              <g fill="#42526b" fontSize="14" fontWeight="700">
                <text x="63" y="240">Jan</text>
                <text x="130" y="240">Feb</text>
                <text x="197" y="240">Mar</text>
                <text x="264" y="240">Apr</text>
                <text x="331" y="240">May</text>
                <text x="379" y="240">Jun</text>
              </g>
              <path d="M68 166 L95 146 L122 152 L149 112 L176 129 L203 119 L230 98 L257 64 L284 82 L311 94 L338 52 L365 69 L392 32" fill="none" stroke="#13b49d" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M68 190 L95 173 L122 181 L149 160 L176 134 L203 143 L230 131 L257 112 L284 83 L311 116 L338 98 L365 111 L392 73" fill="none" stroke="#2176ff" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M68 214 L95 202 L122 203 L149 200 L176 184 L203 188 L230 181 L257 185 L284 161 L311 179 L338 157 L365 154 L392 130" fill="none" stroke="#9254ff" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
              <g>
                {[
                  ['#13b49d', 68, 166], ['#13b49d', 95, 146], ['#13b49d', 122, 152], ['#13b49d', 149, 112], ['#13b49d', 176, 129], ['#13b49d', 203, 119], ['#13b49d', 230, 98], ['#13b49d', 257, 64], ['#13b49d', 284, 82], ['#13b49d', 311, 94], ['#13b49d', 338, 52], ['#13b49d', 365, 69], ['#13b49d', 392, 32],
                  ['#2176ff', 68, 190], ['#2176ff', 95, 173], ['#2176ff', 122, 181], ['#2176ff', 149, 160], ['#2176ff', 176, 134], ['#2176ff', 203, 143], ['#2176ff', 230, 131], ['#2176ff', 257, 112], ['#2176ff', 284, 83], ['#2176ff', 311, 116], ['#2176ff', 338, 98], ['#2176ff', 365, 111], ['#2176ff', 392, 73],
                  ['#9254ff', 68, 214], ['#9254ff', 95, 202], ['#9254ff', 122, 203], ['#9254ff', 149, 200], ['#9254ff', 176, 184], ['#9254ff', 203, 188], ['#9254ff', 230, 181], ['#9254ff', 257, 185], ['#9254ff', 284, 161], ['#9254ff', 311, 179], ['#9254ff', 338, 157], ['#9254ff', 365, 154], ['#9254ff', 392, 130],
                ].map(([fill, cx, cy], index) => (
                  <circle key={`${fill}-${index}`} cx={cx} cy={cy} r="5" fill={fill} />
                ))}
              </g>
              <g fontSize="13" fontWeight="750" fill="#1f2a44">
                <circle cx="82" cy="46" r="6" fill="#13b49d" /><text x="98" y="51">US</text>
                <circle cx="82" cy="76" r="6" fill="#2176ff" /><text x="98" y="81">EMEA</text>
                <circle cx="82" cy="106" r="6" fill="#9254ff" /><text x="98" y="111">APAC</text>
              </g>
            </svg>
          </div>
        </div>
        <div className="mockPanel mockPanel--donut">
          <div className="mockPanel__topline"><strong>Revenue by Region</strong></div>
          <div className="donutVisual" aria-hidden="true"><span>$12.4M<br />Total</span></div>
          <ul className="miniLegend">
            <li><span /> US <b>48%</b></li>
            <li><span /> EMEA <b>30%</b></li>
            <li><span /> APAC <b>22%</b></li>
          </ul>
        </div>
        <div className="mockPanel mockPanel--bars">
          <div className="mockPanel__topline"><strong>Top Products</strong></div>
          <div className="barChart" aria-hidden="true">
            {[
              ['Product A', '94%'],
              ['Product B', '72%'],
              ['Product C', '54%'],
              ['Product D', '40%'],
              ['Product E', '27%'],
            ].map(([label, width]) => (
              <div className="barChart__row" key={label}>
                <span>{label}</span>
                <i style={{'--w': width}} />
              </div>
            ))}
          </div>
          <div className="barAxis" aria-hidden="true"><span>0</span><span>2M</span><span>4M</span><span>6M</span></div>
        </div>
      </div>
      <div className="heroOutputPills" aria-label="Supported output surfaces">
        {outputSurfaces.map(([type, label]) => (
          <span key={type}>
            <OutputIcon type={type} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

function HomepageHeader() {
  return (
    <header className="landingHero">
      <div className="container landingHero__layout">
        <div className="landingHero__content">
          <p className="eyebrow eyebrow--pill">SQL-native · open source · community driven</p>
          <h1>A Semantic Visualization Layer for Analytical Systems</h1>
          <p className="landingHero__lead">
            Integrate GGSQL with the dbt ecosystem. Author SQL-based visualizations. Build dashboard specs that preserve analytics lineage.
          </p>
          <div className="buttonRow">
            <Link className="button button--primary button--lg" to="/docs/get-started/quickstart">
              Get Started <span aria-hidden="true">→</span>
            </Link>
            <Link className="button button--secondary button--lg heroGithubButton" to="https://github.com/kannandreams/glyf">
              ☆ Star on GitHub
            </Link>
          </div>
          <div className="heroMeta" aria-label="Project qualities">
            <span>Open source</span>
            <span>Apache-2.0</span>
            <span>Python 3.11+</span>
            <span>Rust powered</span>
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
