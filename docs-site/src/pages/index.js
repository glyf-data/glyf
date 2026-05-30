import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

const featureSections = [
  {
    id: 'integration',
    tag: 'integration',
    title: 'Your dbt project is the source of truth.',
    description:
      'Glyf reads your dbt manifest directly. Charts reference models the same way dbt models reference each other, with ref(). No copy-pasting SQL and no schema drift.',
    items: [
      {
        name: 'dbt ref() in every chart',
        desc: 'Use {{ ref(\'model\') }} in chart SQL exactly as you would in a dbt model. Glyf resolves each reference to its schema path and validates the query before publish.',
        status: 'live',
        reverse: false,
        visual: 'chartSql',
        filename: 'charts/revenue_weekly.glyf.sql',
      },
      {
        name: 'Version controlled, reviewable',
        desc: 'Chart definitions, layouts, and macros live in Git alongside your dbt project. Reviewers see exact SQL and YAML diffs, not just screenshots.',
        status: 'live',
        reverse: true,
        visual: 'gitDiff',
        filename: 'terminal — git diff',
      },
    ],
  },
  {
    id: 'exports',
    tag: 'exports',
    title: 'Charts that live anywhere.',
    description:
      'No BI server to maintain. Glyf builds self-contained artifacts that teams can host in docs, apps, CI pipelines, or static storage.',
    items: [
      {
        name: 'Zero-server static output',
        desc: 'Each glyf build produces self-contained HTML files with data and rendering logic inlined. Drop them into any static host and they just work.',
        status: 'live',
        reverse: false,
        visual: 'buildOutput',
        filename: 'terminal',
      },
      {
        name: 'Generated React components',
        desc: 'Glyf compiles dashboards to typed .tsx components with inferred prop interfaces. Drop them into your product codebase with no BI SDK dependency.',
        status: 'live',
        reverse: true,
        visual: 'tsxOutput',
        filename: 'dist/RevenueWeekly.tsx — auto-generated',
      },
    ],
  },
  {
    id: 'customization',
    tag: 'customization',
    title: 'Dashboard logic as reviewed code.',
    description:
      'Thresholds, color mappings, and conditional labels all live in Python macros and YAML specs. Reusable, testable, and visible in code review.',
    items: [
      {
        name: 'Programmable Python macros',
        desc: 'Define reusable chart logic like color mappings, thresholds, and conditional labels as Python functions that are typed, tested, and reviewed.',
        status: 'live',
        reverse: false,
        visual: 'pythonMacros',
        filename: 'macros/thresholds.py',
      },
      {
        name: 'Dashboard YAML specs',
        desc: 'Define layout, chart ordering, visibility conditions, and macro bindings declaratively in YAML. Changing a dashboard becomes a one-line diff.',
        status: 'live',
        reverse: true,
        visual: 'dashboardYaml',
        filename: 'dashboards/growth.yaml',
      },
    ],
  },
  {
    id: 'observability',
    tag: 'observability',
    title: 'Know when something breaks or shifts.',
    description:
      'Every build can produce visual diffs and alert hooks. Catch regressions in CI before a dashboard change reaches stakeholders.',
    items: [
      {
        name: 'Visual diff as a build artifact',
        desc: 'Every glyf build can generate a side-by-side visual diff against the previous build, highlighting metric shifts, new categories, and trend reversals.',
        status: 'live',
        reverse: false,
        visual: 'visualDiff',
        filename: 'artifacts/visual-diff — build #84 vs #83',
      },
      {
        name: 'Pipeline hooks and alerts',
        desc: 'Declare Slack or webhook alerts directly in dashboard YAML. Conditions are evaluated against query results at build time with severity-based routing.',
        status: 'live',
        reverse: true,
        visual: 'alertsYaml',
        filename: 'dashboards/revenue.yaml — alerts block',
      },
    ],
  },
  {
    id: 'ai',
    tag: 'ai',
    title: 'Agents that understand your chart graph.',
    description:
      'Glyf exposes a spec graph over MCP so agents can reason about model-to-chart dependencies, assess downstream impact, and open informed pull requests.',
    items: [
      {
        name: 'Agent-ready MCP server',
        desc: 'Agents can list charts, fetch specs, and query upstream model dependencies. impact_of_model() returns every downstream chart affected by a schema change.',
        status: 'soon',
        reverse: false,
        visual: 'mcpImpact',
        filename: 'MCP session — Claude Agent ↔ Glyf',
      },
      {
        name: 'Natural language chart edits',
        desc: 'Describe a chart change in plain language. Glyf translates it to a SQL diff, validates the build, attaches the visual diff, and opens a pull request.',
        status: 'soon',
        reverse: true,
        visual: 'mcpEdit',
        filename: 'MCP session — natural language edit',
      },
    ],
  },
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
  ['BI platforms set the terms', 'BI platforms turn simple publishing into procurement. Glyf keeps visualization output as files your team can build, review, and host.'],
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
    <div className="heroCodeVisual" aria-label="Glyf build workflow diagram">
      <div className="heroCodeWindow">
        <img
          className="heroDiagramImage"
          src="/img/glyf-hero-diagram-v3.svg"
          alt="Diagram showing Glyf workflow from data sources through dbt and chart composition to generated outputs."
        />
      </div>
    </div>
  );
}

function FeatureMacWindow({filename, children}) {
  return (
    <div className="featureMacWindow">
      <div className="featureMacTitlebar">
        <span className="featureMacDot featureMacDot--red" />
        <span className="featureMacDot featureMacDot--yellow" />
        <span className="featureMacDot featureMacDot--green" />
        <span className="featureMacFilename">{filename}</span>
      </div>
      <div className="featureMacBody">{children}</div>
    </div>
  );
}

function FeatureDiffVisual() {
  return (
    <div className="featureDiffVisual">
      <div className="featureDiffColumn">
        <div className="featureDiffLabel">Build #83 — before</div>
        <div className="featureMiniChart">
          {[55, 72, 60, 85, 90, 78, 82].map((height) => (
            <span className="featureMiniBar featureMiniBar--before" key={`before-${height}`} style={{height: `${height}%`}} />
          ))}
        </div>
      </div>
      <div className="featureDiffColumn">
        <div className="featureDiffLabel">Build #84 — after</div>
        <div className="featureMiniChart">
          {[55, 72, 60, 85, 44, 78, 82].map((height, index) => (
            <span
              className={`featureMiniBar${index === 4 ? ' featureMiniBar--drop' : ' featureMiniBar--after'}`}
              key={`after-${height}-${index}`}
              style={{height: `${height}%`}}
            />
          ))}
        </div>
        <div className="featureAnnotation">week 5 dropped 47%{'\n'}new category introduced — review needed</div>
      </div>
    </div>
  );
}

function FeatureMcpTrace({variant}) {
  if (variant === 'edit') {
    return (
      <div className="featureMcpTrace">
        <div className="featureMcpLine">
          <span className="featureMcpRole featureMcpRole--agent">agent</span>
          <span className="featureMcpMessage">"Change revenue_weekly to group by month and add a plan breakdown"</span>
        </div>
        <div className="featureMcpLine">
          <span className="featureMcpRole featureMcpRole--glyf">glyf</span>
          <span className="featureMcpMessage featureMcpMessage--dim">→ patch revenue_weekly.glyf.sql</span>
        </div>
        <div className="featureMcpLine">
          <span className="featureMcpRole" />
          <span className="featureMcpMessage featureMcpMessage--ok">+ GROUP BY date_trunc('month', ...), plan_name</span>
        </div>
        <div className="featureMcpLine">
          <span className="featureMcpRole" />
          <span className="featureMcpMessage featureMcpMessage--danger">- GROUP BY date_trunc('week', ...)</span>
        </div>
        <div className="featureMcpLine">
          <span className="featureMcpRole featureMcpRole--glyf">glyf</span>
          <span className="featureMcpMessage featureMcpMessage--dim">→ build passed — visual diff attached</span>
        </div>
        <div className="featureMcpLine">
          <span className="featureMcpRole featureMcpRole--result">result</span>
          <span className="featureMcpMessage featureMcpMessage--dim">PR opened with diff + visual artifact</span>
        </div>
      </div>
    );
  }

  return (
    <div className="featureMcpTrace">
      <div className="featureMcpLine">
        <span className="featureMcpRole featureMcpRole--agent">agent</span>
        <span className="featureMcpMessage">list_charts()</span>
      </div>
      <div className="featureMcpLine">
        <span className="featureMcpRole featureMcpRole--glyf">glyf</span>
        <span className="featureMcpMessage featureMcpMessage--dim">→ revenue_weekly, signups_by_plan, churn_cohort, mrr_breakdown (+9)</span>
      </div>
      <div className="featureMcpLine">
        <span className="featureMcpRole featureMcpRole--agent">agent</span>
        <span className="featureMcpMessage">impact_of_model("orders")</span>
      </div>
      <div className="featureMcpLine">
        <span className="featureMcpRole featureMcpRole--glyf">glyf</span>
        <span className="featureMcpMessage featureMcpMessage--dim">→ affects 4 charts: revenue_weekly, mrr_breakdown, ltv_by_cohort, arpu</span>
      </div>
      <div className="featureMcpLine">
        <span className="featureMcpRole featureMcpRole--result">result</span>
        <span className="featureMcpMessage featureMcpMessage--dim">agent opens PR annotating all downstream charts automatically</span>
      </div>
    </div>
  );
}

function FeatureVisual({item}) {
  switch (item.visual) {
    case 'chartSql':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeMuted">-- reference dbt models directly in chart SQL</span>{'\n'}
<span className="codeKw">SELECT</span>{'\n'}
{'  '}date_trunc(<span className="codeStr">'week'</span>, o.created_at) <span className="codeKw">AS</span> week,{'\n'}
{'  '}sum(o.revenue_usd) <span className="codeKw">AS</span> revenue,{'\n'}
{'  '}p.plan_name{'\n'}
<span className="codeKw">FROM</span> <span className="codeRef">{'{{ ref(\'orders\') }}'}</span> o{'\n'}
<span className="codeKw">JOIN</span> <span className="codeRef">{'{{ ref(\'plans\') }}'}</span> p{'\n'}
{'  '}<span className="codeKw">ON</span> o.plan_id = p.id{'\n'}
<span className="codeKw">GROUP BY</span> <span className="codeNum">1</span>, <span className="codeNum">3</span>{'\n\n'}
<span className="codeMuted">────────────────────────────</span>{'\n'}
<span className="codeOk">✓</span> resolved orders → analytics.orders{'\n'}
<span className="codeOk">✓</span> resolved plans → analytics.plans{'\n'}
<span className="codeOk">✓</span> query valid — 0 errors</code></pre>
        </FeatureMacWindow>
      );
    case 'gitDiff':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeFn">$</span> git diff main..feat/q3-charts{'\n\n'}
<span className="featureDiffLine featureDiffLine--context">  charts/revenue_weekly.glyf.sql</span>{'\n'}
<span className="featureDiffLine featureDiffLine--remove">- GROUP BY date_trunc('week', created_at)</span>{'\n'}
<span className="featureDiffLine featureDiffLine--add">+ GROUP BY date_trunc('month', created_at)</span>{'\n\n'}
<span className="featureDiffLine featureDiffLine--context">  dashboards/growth.yaml</span>{'\n'}
<span className="featureDiffLine featureDiffLine--add">+ - id: new_mrr_cohort</span>{'\n'}
<span className="featureDiffLine featureDiffLine--add">+   sql: ./new_mrr_cohort.sql</span>{'\n\n'}
<span className="codeMuted">2 files changed, 3 insertions(+), 1 deletion(-)</span>{'\n\n'}
<span className="codeOk">✓</span> glyf build passed — 14 charts{'\n'}
<span className="codeOk">✓</span> visual diff → artifacts/diff.html{'\n'}
<span className="codeMuted">Ready to merge.</span></code></pre>
        </FeatureMacWindow>
      );
    case 'buildOutput':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeFn">$</span> glyf build --target prod{'\n\n'}
<span className="codeMuted">Building 12 charts...</span>{'\n'}
<span className="codeOk">✓</span> revenue_weekly{'\n'}
<span className="codeOk">✓</span> signups_by_plan{'\n'}
<span className="codeOk">✓</span> churn_cohort{'\n'}
<span className="codeMuted">  ... 9 more</span>{'\n\n'}
<span className="codeMuted">Exporting static assets...</span>{'\n'}
<span className="codeOk">✓</span> dist/revenue_weekly.html <span className="codeMuted">42kb</span>{'\n'}
<span className="codeOk">✓</span> dist/signups_by_plan.html <span className="codeMuted">38kb</span>{'\n'}
<span className="codeOk">✓</span> dist/index.html <span className="codeMuted">8kb</span>{'\n'}
<span className="codeOk">✓</span> dist/charts.zip <span className="codeMuted">180kb</span>{'\n\n'}
<span className="codeMuted">No server required.</span>{'\n'}
<span className="codeMuted">Drop into S3, Notion, GitHub Pages, or CI artifacts.</span></code></pre>
        </FeatureMacWindow>
      );
    case 'tsxOutput':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeMuted">// generated by glyf — do not edit manually</span>{'\n'}
<span className="codeKw">import</span> {'{ '}<span className="codeFn">GlyfChart</span>{' } '}<span className="codeKw">from</span> <span className="codeStr">'@glyf/react'</span>{'\n\n'}
<span className="codeKw">export interface</span> <span className="codeFn">RevenueWeeklyProps</span> {'{'}{'\n'}
{'  '}startDate?: <span className="codeVar">string</span>{'\n'}
{'  '}planFilter?: <span className="codeVar">string</span>[] {'\n'}
{'}'}{'\n\n'}
<span className="codeKw">export function</span> <span className="codeFn">RevenueWeekly</span>({'{ '}startDate, planFilter {'}'}) {'{'}{'\n'}
{'  '}<span className="codeKw">return</span> ({'\n'}
{'    '}&#60;<span className="codeFn">GlyfChart</span>{'\n'}
{'      '}spec=<span className="codeStr">"revenue_weekly"</span>{'\n'}
{'      '}params={'{'}{'{ '}startDate, planFilter {'}'}{'}'}{'\n'}
{'    '}/&#62;{'\n'}
{'  '}){'\n'}
{'}'}{'\n\n'}
<span className="codeMuted">// typed props, no BI SDK dependency</span></code></pre>
        </FeatureMacWindow>
      );
    case 'pythonMacros':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeKw">from</span> glyf <span className="codeKw">import</span> macro, ChartContext{'\n\n'}
<span className="codeFn">@macro</span>{'\n'}
<span className="codeKw">def</span> <span className="codeFn">plan_color</span>(ctx: <span className="codeVar">ChartContext</span>, plan: <span className="codeVar">str</span>) -&gt; <span className="codeVar">str</span>:{'\n'}
{'  '}<span className="codeKw">return</span> {'{'}{'\n'}
{'    '}<span className="codeStr">"starter"</span>: <span className="codeStr">"#94a3b8"</span>,{'\n'}
{'    '}<span className="codeStr">"growth"</span>: <span className="codeStr">"#6366f1"</span>,{'\n'}
{'    '}<span className="codeStr">"enterprise"</span>: <span className="codeStr">"#0ea5e9"</span>,{'\n'}
{'  }'}.get(plan, <span className="codeStr">"#e2e8f0"</span>){'\n\n'}
<span className="codeFn">@macro</span>{'\n'}
<span className="codeKw">def</span> <span className="codeFn">alert_threshold</span>(ctx: <span className="codeVar">ChartContext</span>) -&gt; <span className="codeVar">float</span>:{'\n'}
{'  '}<span className="codeKw">return</span> ctx.config[<span className="codeStr">"alert_pct"</span>]{'\n\n'}
<span className="codeRef">{'{{ plan_color(\'growth\') }}'}</span> <span className="codeMuted">-- → "#6366f1"</span></code></pre>
        </FeatureMacWindow>
      );
    case 'dashboardYaml':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code>title: <span className="codeStr">Growth Overview</span>{'\n'}
layout: <span className="codeVar">2col</span>{'\n\n'}
charts:{'\n'}
{'  '}- id: <span className="codeStr">revenue_weekly</span>{'\n'}
{'    '}sql: <span className="codeStr">./revenue_weekly.sql</span>{'\n'}
{'    '}title: <span className="codeStr">Weekly Revenue</span>{'\n'}
{'    '}color_macro: <span className="codeFn">plan_color</span>{'\n\n'}
{'  '}- id: <span className="codeStr">churn_cohort</span>{'\n'}
{'    '}sql: <span className="codeStr">./churn_cohort.sql</span>{'\n'}
{'    '}visible_if: <span className="codeStr">"user.plan == \'enterprise\'"</span>{'\n\n'}
<span className="codeOk">✓</span> <span className="codeMuted">dashboard spec validated — 3 charts</span></code></pre>
        </FeatureMacWindow>
      );
    case 'visualDiff':
      return (
        <FeatureMacWindow filename={item.filename}>
          <FeatureDiffVisual />
        </FeatureMacWindow>
      );
    case 'alertsYaml':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code>charts:{'\n'}
{'  '}- id: <span className="codeStr">revenue_weekly</span>{'\n'}
{'    '}sql: <span className="codeStr">./revenue_weekly.sql</span>{'\n'}
{'    '}alerts:{'\n'}
{'      '}- <span className="codeKw">channel</span>: <span className="codeStr">"#data-alerts"</span>{'\n'}
{'        '}<span className="codeKw">condition</span>: <span className="codeStr">"wow_pct &lt; -0.10"</span>{'\n'}
{'        '}<span className="codeKw">message</span>: <span className="codeStr">"Revenue dropped &gt;10% WoW"</span>{'\n'}
{'        '}<span className="codeKw">severity</span>: <span className="codeWarn">warn</span>{'\n\n'}
{'      '}- <span className="codeKw">channel</span>: <span className="codeStr">"#incidents"</span>{'\n'}
{'        '}<span className="codeKw">condition</span>: <span className="codeStr">"wow_pct &lt; -0.25"</span>{'\n'}
{'        '}<span className="codeKw">message</span>: <span className="codeStr">"Revenue dropped &gt;25% — investigate"</span>{'\n'}
{'        '}<span className="codeKw">severity</span>: <span className="codeHi">critical</span>{'\n\n'}
<span className="codeOk">✓</span> alert registered revenue_weekly / warn{'\n'}
<span className="codeOk">✓</span> alert registered revenue_weekly / critical</code></pre>
        </FeatureMacWindow>
      );
    case 'mcpImpact':
      return (
        <FeatureMacWindow filename={item.filename}>
          <FeatureMcpTrace variant="impact" />
        </FeatureMacWindow>
      );
    case 'mcpEdit':
      return (
        <FeatureMacWindow filename={item.filename}>
          <FeatureMcpTrace variant="edit" />
        </FeatureMacWindow>
      );
    default:
      return (
        <FeatureMacWindow filename={item.filename}>
          <div className="featureImgPlaceholder">
            <span className="featureImgPlaceholderIcon">□</span>
            <span className="featureImgPlaceholderLabel">replace with product screenshot</span>
          </div>
        </FeatureMacWindow>
      );
  }
}

function HomepageHeader() {
  return (
    <header className="landingHero">
      <div className="container landingHero__layout">
        <div className="landingHero__content">
          <p className="heroKicker">visualization build step to data pipeline</p>
          <h1>
            <span>Ship charts</span>
            <span className="heroHeadlineAccent">from the same pipeline</span>
            <span>as your data.</span>
          </h1>
          <div className="landingHero__installBlock" aria-label="Install Glyf">
            <pre><code>uv install glyf</code></pre>
          </div>
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
          <p className="eyebrow">the problem</p>
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
  const [activeFeatureSection, setActiveFeatureSection] = React.useState(featureSections[0].id);
  const featureRootRef = React.useRef(null);

  React.useEffect(() => {
    const root = featureRootRef.current;
    if (!root || typeof IntersectionObserver === 'undefined') {
      return undefined;
    }

    const sections = root.querySelectorAll('[data-feature-anchor]');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveFeatureSection(entry.target.id);
          }
        });
      },
      {rootMargin: '-35% 0px -55% 0px', threshold: 0},
    );

    sections.forEach((section) => observer.observe(section));

    return () => {
      sections.forEach((section) => observer.unobserve(section));
      observer.disconnect();
    };
  }, []);

  return (
    <section className="featuresSection" ref={featureRootRef}>
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">features</p>
          <h2>What makes Glyf different.</h2>
          <p>
            Core build-step features are available today. Roadmap items show where Glyf is heading.
            Each section below shows exactly what the feature looks like in practice.
          </p>
        </div>
        <div className="featureStoryNav" role="navigation" aria-label="Feature section anchors">
          <a className="featureStoryLogo" href="#features-top">
            Glyf
          </a>
          <div className="featureStoryNavLinks">
            {featureSections.map((section) => (
              <a
                className={`featureStoryNavLink${section.id === activeFeatureSection ? ' is-active' : ''}`}
                href={`#${section.id}`}
                key={section.id}
                onClick={() => setActiveFeatureSection(section.id)}
              >
                {section.tag}
              </a>
            ))}
          </div>
        </div>
        <div className="featureStories" id="features-top">
          {featureSections.map((section) => (
            <article className="featureStorySection" data-feature-anchor id={section.id} key={section.id}>
              <div className="featureStoryHeader">
                <div className="featureStoryTag">{section.tag}</div>
                <h3>{section.title}</h3>
                <p>{section.description}</p>
              </div>
              <div className="featureStoryBlocks">
                {section.items.map((item) => (
                  <div className={`featureStoryBlock${item.reverse ? ' is-reverse' : ''}`} key={`${section.id}-${item.name}`}>
                    <div className="featureStoryVisual">
                      <FeatureVisual item={item} />
                    </div>
                    <div className="featureStoryNote">
                      <div className="featureStoryName">{item.name}</div>
                      <p className="featureStoryDesc">{item.desc}</p>
                      <span className={`featureStoryStatus${item.status === 'soon' ? ' is-soon' : ''}`}>{item.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
          <div className="featureStoryFooter">
            <Link className="featureStoryFooterButton" to="/docs/resources/roadmap">
              View roadmap &rarr;
            </Link>
            <span className="featureStoryFooterCount">{featureSections.length} sections</span>
          </div>
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
          <p className="eyebrow">how it works</p>
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
            <FeatureMacWindow filename="sessions_by_plan.ggsql">
              <pre><code><span className="codeKw">SELECT</span> plan, <span className="codeFn">sum</span>(sessions){'\n'}
<span className="codeKw">FROM</span> <span className="codeRef">{'{{ ref(\'fct_usage\') }}'}</span>{'\n'}
<span className="codeKw">GROUP BY</span> 1{'\n\n'}
<span className="codeClause">VISUALISE</span> plan <span className="codeKw">AS</span> x{'\n'}
<span className="codeClause">DRAW</span> pie{'\n'}
<span className="codeClause">LABEL</span> title <span className="codeOp">=&gt;</span> <span className="codeStr">'Sessions by Plan'</span></code></pre>
            </FeatureMacWindow>
          </article>
          <article className="howCodeStep">
            <span>{workflowSteps[1][0]}</span>
            <h3>{workflowSteps[1][1]}</h3>
            <p>{workflowSteps[1][2]}</p>
            <FeatureMacWindow filename="product.yml">
              <pre><code><span className="codeKw">sections</span>:{'\n'}
{'  '}- title: <span className="codeStr">Activation</span>{'\n'}
{'    '}items:{'\n'}
{'      '}- component:{'\n'}
{'          '}<span className="codeFn">{'{{ activation_health(0.82) }}'}</span>{'\n'}
{'      '}- chart: sessions_by_plan{'\n'}
{'      '}- chart: active_users</code></pre>
            </FeatureMacWindow>
          </article>
          <article className="howCodeStep">
            <span>{workflowSteps[2][0]}</span>
            <h3>{workflowSteps[2][1]}</h3>
            <p>{workflowSteps[2][2]}</p>
            <FeatureMacWindow filename="Terminal">
              <pre><code><span className="codeFn">$</span> glyf build{'\n\n'}
<span className="codeMuted">✓ Resolved 6 ref() calls</span>{'\n'}
<span className="codeMuted">✓ Compiled 8 charts</span>{'\n'}
<span className="codeMuted">✓ Built product.html</span>{'\n'}
<span className="codeMuted">✓ Wrote chart assets</span>{'\n'}
<span className="codeFn">✓ Build complete in 2.1s</span></code></pre>
            </FeatureMacWindow>
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
          <p className="eyebrow">who it's for</p>
          <h2>Built for every role in the data team.</h2>
        </div>
        <div className="personasGrid">
          {personas.map(([role, title, description]) => (
            <article className="personaCard" key={role}>
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
          <p className="eyebrow">glyf + ggsql</p>
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
          <p className="eyebrow">documentation</p>
          <h2>Start with the docs you need.</h2>
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
          <p className="eyebrow">examples gallery</p>
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
      title="Ship charts from the same pipeline as your data"
      description="Glyf is the open-source build step for dbt-aware visualization artifacts."
    >
      <HomepageHeader />
      <main>
        <HowItWorks />
        <FeaturesSection />
        <GgsqlSection />
        <PersonasSection />
        <Examples />
      </main>
    </Layout>
  );
}
