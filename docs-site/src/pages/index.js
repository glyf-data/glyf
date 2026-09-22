import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import useBaseUrl from '@docusaurus/useBaseUrl';

const featureSections = [
  {
    id: 'integration',
    tag: 'integration',
    label: 'Integration',
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
        filename: 'charts/revenue_weekly.ggsql',
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
    id: 'ai',
    tag: 'ai',
    label: 'AI',
    title: 'Agents that understand your chart graph.',
    description:
      'Glyf will expose a spec graph over MCP so agents can reason about model-to-chart dependencies, assess downstream impact, and open informed pull requests.',
    items: [
      {
        name: 'Agent-ready MCP server',
        desc: 'Agents will list charts, fetch specs, and query upstream model dependencies. impact_of_model() will return every downstream chart affected by a schema change.',
        status: 'soon',
        reverse: false,
        visual: 'mcpImpact',
        filename: 'MCP session — Claude Agent ↔ Glyf',
      },
      {
        name: 'Natural language chart edits',
        desc: 'Describe a chart change in plain language. Glyf will translate it to a SQL diff, validate the build, attach the visual diff, and open a pull request.',
        status: 'soon',
        reverse: true,
        visual: 'mcpEdit',
        filename: 'MCP session — natural language edit',
      },
    ],
  },
  {
    id: 'exports',
    tag: 'exports',
    label: 'Exports',
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
        name: 'React components',
        desc: '@glyf/react loads the bundle.json every build writes and renders its charts with GlyfProvider and GlyfChart, as SVG or PNG. No BI SDK and no server.',
        status: 'preview',
        reverse: true,
        visual: 'reactEmbed',
        filename: 'app/Analytics.tsx',
      },
    ],
  },
  {
    id: 'customization',
    tag: 'customization',
    label: 'Customization',
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
    id: 'visual-diff',
    tag: 'review',
    label: 'Visual diff',
    title: 'Review the pictures, not just the SQL.',
    description:
      'A change to a model or a chart can move a number on a dashboard without touching any file a reviewer would open. Glyf compares every chart in a pull request with the base branch and reports which changed, how much of each picture moved, and why.',
    items: [
      {
        name: 'A diff that says what moved, and why',
        desc: 'First in the chart\'s terms: bars gone, points higher or lower, and which series. Then the rows: a missing category, a column total, the row count. Then why: the query changed, the rows changed, or only the chart definition did. The same data renders to the same bytes, so an unchanged chart is never reported.',
        status: 'live',
        reverse: false,
        visual: 'visualDiffTerminal',
        filename: 'terminal — glyf diff',
        links: [['Add it to your pull requests', '/docs/guides/visual-diff']],
      },
      {
        name: 'Before, after, and what moved',
        desc: 'Every changed chart is drawn three times: as it was, as it is, and as it is over its old self, the baseline in grey behind the new marks and every category that moved boxed. A series that disappeared stays in the legend with nothing under it. One workflow file puts a summary on the pull request and the full report in its artifacts.',
        status: 'live',
        reverse: true,
        visual: 'visualDiffReport',
        filename: 'target/glyf/diff/index.html',
        links: [['See it on a real pull request', 'https://github.com/glyf-data/glyf/pull/175']],
      },
    ],
  },
  {
    id: 'data-protection',
    tag: 'governance',
    label: 'Data protection',
    title: 'Decide what leaves the warehouse. The build enforces it.',
    description:
      'A published dashboard is a file anyone with the link can read. Glyf treats what that file contains as part of the build: which rows it holds, which columns count as personal data, and what happens when a chart reaches for one. Every rule is in glyf.yml, reviewed like the rest.',
    items: [
      {
        name: 'A chart cannot ship personal data by accident',
        desc: 'Columns tagged pii in your dbt schema, or listed in glyf.yml, are known to every build. A query that returns one fails the build naming the chart and the column, or, with on_pii: redact, publishes it masked. A value scan warns about the columns nobody tagged that look like emails, phone or card numbers.',
        status: 'live',
        reverse: false,
        visual: 'piiDeny',
        filename: 'terminal — glyf build',
        links: [['Keeping PII out of a chart', '/docs/reference/configuration#keeping-pii-out-of-a-chart']],
      },
      {
        name: 'Ship the picture, or the plotted columns, or every row',
        desc: 'export.row_data sets what a published site carries. include keeps the rows behind each chart for interactive use. minimal keeps only the columns a chart draws, so a query that selects more than it plots does not publish the rest. exclude ships rendered images and nothing else. bundle.json records which one the build used, so a reviewer can check.',
        status: 'live',
        reverse: true,
        visual: 'rowDataModes',
        filename: 'glyf.yml → target/glyf/site',
        links: [['Data exposure guide', '/docs/guides/data-exposure']],
      },
    ],
  },
];

const roadmapItems = [
  ['Pipeline alerts', 'Alert conditions declared in dashboard YAML, evaluated against query results at build time and routed by severity.', 'https://github.com/glyf-data/glyf/issues/137'],
];

// Open feature requests, most upvoted first; the template applies the "feature request" label.
const roadmapIssuesUrl = 'https://github.com/glyf-data/glyf/issues?q=is%3Aissue+is%3Aopen+label%3A%22feature+request%22+sort%3Areactions-%2B1-desc';
const featureRequestUrl = 'https://github.com/glyf-data/glyf/issues/new?template=feature_request.yml';

const featureLinks = [
  ['Quickstart', 'Run the included analytical project and render your first dashboard.', '/docs/get-started/quickstart'],
  ['Command reference', 'See every CLI command, option, and common workflow.', '/docs/reference/cli'],
  ['Technical guide', 'Understand parsing, dbt artifact resolution, rendering, and output paths.', '/docs/guides/technical-architecture'],
  ['Chart syntax', 'The GGSQL format, and the chart types and interactions Glyf adds to it.', '/docs/guides/visualisation-syntax'],
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
  ['01 — Chart Definition', 'Write charts in GGSQL', 'SQL you already know, then a few lines saying what to draw. Use ref() to reference dbt models directly.'],
  ['02 — Dashboard Layout', 'Compose in YAML + Python', 'Lay out charts into sections. Use Python macros for conditional logic, thresholds, and reusable components.'],
  ['03 — Build Output', 'Run one command', 'Glyf resolves dbt artifacts, validates chart specs, renders charts, and emits the files you can publish.'],
];

const personas = [
  ['Analytics Engineer', 'You work in dbt. Glyf is your next step.', 'You know SQL. You version-control everything. You should not need LookML or a BI platform UI to publish a declared dashboard artifact.'],
  ['Data Scientist', 'Charts in SQL, not one-off notebooks.', 'Write SQL-style chart definitions that run in the pipeline, stay current, and live beside the models they query.'],
  ['Data Leader', 'Reduce platform dependency.', 'Glyf is open source, runs locally, and produces outputs your team already knows how to deploy and review.'],
  ['Application Engineer', 'Import or publish a dashboard artifact.', 'The data team owns the spec. You fetch bundle.json and show the SVG or PNG it points to, without an embedded analytics vendor.'],
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

const heroInputs = [
  {icon: 'dbt', title: 'dbt models', detail: 'Your data models'},
  {icon: 'declarative', title: 'YAML layouts', detail: 'Define charts & pages'},
  {icon: 'code', title: 'Python macros', detail: 'Transform & extend'},
  {icon: 'database', title: 'Warehouse data', detail: 'DuckDB · Snowflake · BigQuery', tag: 'Apache Arrow'},
];

const heroTraits = [
  ['bolt', 'Code-first'],
  ['engine', 'Rust engine'],
  ['agent', 'Agent-ready'],
  ['server', 'No BI server'],
];

// Brand marks from Simple Icons (CC0), https://simpleicons.org
const heroDestinations = [
  {
    name: 'Amazon S3',
    color: '#569A31',
    path: 'M20.913 13.147l.12-.895c.947.576 1.258.922 1.354 1.071-.16.031-.562.046-1.474-.176zm-2.174 7.988a.547.547 0 0 0-.005.073c0 .084-.207.405-1.124.768a10.28 10.28 0 0 1-1.438.432c-1.405.325-3.128.504-4.853.504-4.612 0-7.412-1.184-7.412-1.704a.547.547 0 0 0-.005-.073L1.81 5.602c.135.078.28.154.432.227.042.02.086.038.128.057.134.062.272.122.417.18l.179.069c.154.058.314.114.478.168.043.013.084.029.13.043.207.065.423.127.646.187l.176.044c.175.044.353.087.534.127a23.414 23.414 0 0 0 .843.17l.121.023c.252.045.508.085.768.122.071.011.144.02.216.03.2.027.4.053.604.077l.24.027c.245.026.49.05.74.07l.081.009c.275.022.552.04.83.056l.233.012c.21.01.422.018.633.025a33.088 33.088 0 0 0 2.795-.026l.232-.011c.278-.016.555-.034.83-.056l.08-.008c.25-.02.497-.045.742-.072l.238-.026c.205-.024.408-.05.609-.077.07-.01.141-.019.211-.03.261-.037.519-.078.772-.122l.111-.02c.215-.04.427-.082.634-.125l.212-.047c.186-.041.368-.085.546-.13l.166-.042c.225-.06.444-.122.654-.189.04-.012.077-.026.115-.038a10.6 10.6 0 0 0 .493-.173c.058-.021.114-.044.17-.066.15-.06.293-.12.43-.185.038-.017.079-.034.116-.052.153-.073.3-.15.436-.228l-.976 7.245c-2.488-.78-5.805-2.292-7.311-3a1.09 1.09 0 0 0-1.088-1.085c-.6 0-1.088.489-1.088 1.088 0 .6.488 1.089 1.088 1.089.196 0 .378-.056.537-.148 1.72.812 5.144 2.367 7.715 3.15zm-7.42-20.047c5.677 0 9.676 1.759 9.75 2.736l-.014.113c-.01.033-.031.067-.048.101-.015.028-.026.057-.047.087-.024.033-.058.068-.09.102-.028.03-.051.06-.084.09-.038.035-.087.07-.133.105-.04.03-.074.06-.119.091-.053.036-.116.071-.177.107-.05.03-.095.06-.15.09-.068.036-.147.073-.222.11-.059.028-.114.057-.177.085-.084.038-.177.074-.268.111-.068.027-.13.054-.203.082-.097.036-.205.072-.31.107-.075.026-.148.053-.228.079-.111.035-.233.069-.35.103-.085.024-.165.05-.253.073-.124.034-.258.065-.389.098-.093.022-.181.046-.278.068-.139.032-.287.061-.433.091-.098.02-.191.041-.293.06-.155.03-.32.057-.482.084-.1.018-.198.036-.302.052-.166.026-.342.048-.515.072-.11.014-.213.03-.325.044-.181.023-.372.041-.56.06-.11.012-.218.025-.332.036-.188.016-.386.029-.58.043-.122.009-.24.02-.364.028-.207.012-.422.02-.635.028-.12.005-.234.012-.354.016a35.605 35.605 0 0 1-2.069 0c-.12-.004-.234-.011-.352-.016-.214-.008-.43-.016-.637-.028-.122-.008-.238-.02-.36-.027-.195-.015-.394-.028-.584-.044-.11-.01-.215-.024-.324-.035-.19-.02-.384-.038-.568-.06l-.315-.044c-.176-.024-.355-.046-.525-.073-.1-.015-.192-.033-.29-.05-.167-.028-.335-.055-.494-.086-.096-.018-.183-.038-.276-.056-.151-.032-.305-.062-.45-.095-.09-.02-.173-.043-.26-.064-.138-.034-.277-.067-.407-.102-.082-.022-.157-.046-.235-.069a11.75 11.75 0 0 1-.368-.108c-.075-.024-.141-.049-.213-.073-.11-.037-.223-.075-.325-.113-.067-.025-.125-.051-.188-.077-.096-.038-.195-.076-.282-.115-.06-.027-.11-.054-.166-.08-.08-.039-.162-.077-.233-.116-.052-.028-.094-.055-.142-.084-.063-.038-.13-.075-.185-.113-.043-.029-.075-.058-.113-.086-.048-.037-.098-.073-.139-.11-.032-.029-.054-.057-.08-.087-.033-.035-.069-.07-.093-.104-.02-.03-.031-.058-.046-.086-.018-.035-.039-.068-.049-.102l-.015-.113c.076-.977 4.074-2.736 9.748-2.736zm12.182 12.124c-.118-.628-.84-1.291-2.31-2.128l.963-7.16a.531.531 0 0 0 .005-.073C22.16 1.581 16.447 0 11.32 0 6.194 0 .482 1.581.482 3.851a.58.58 0 0 0 .005.072L2.819 21.25c.071 2.002 5.236 2.75 8.5 2.75 1.805 0 3.615-.188 5.098-.531.598-.138 1.133-.3 1.592-.48 1.18-.467 1.789-1.053 1.813-1.739l.945-7.018c.557.131 1.016.197 1.389.197.54 0 .902-.137 1.134-.413a.956.956 0 0 0 .21-.804Z',
  },
  {
    name: 'Notion',
    color: '#000000',
    path: 'M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.139c-.093-.514.28-.887.747-.933zM1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z',
  },
  {
    name: 'Cloudflare Pages',
    color: '#F38020',
    path: 'M16.5088 16.8447c.1475-.5068.0908-.9707-.1553-1.3154-.2246-.3164-.6045-.499-1.0615-.5205l-8.6592-.1123a.1559.1559 0 0 1-.1333-.0713c-.0283-.042-.0351-.0986-.021-.1553.0278-.084.1123-.1484.2036-.1562l8.7359-.1123c1.0351-.0489 2.1601-.8868 2.5537-1.9136l.499-1.3013c.0215-.0561.0293-.1128.0147-.168-.5625-2.5463-2.835-4.4453-5.5499-4.4453-2.5039 0-4.6284 1.6177-5.3876 3.8614-.4927-.3658-1.1187-.5625-1.794-.499-1.2026.119-2.1665 1.083-2.2861 2.2856-.0283.31-.0069.6128.0635.894C1.5683 13.171 0 14.7754 0 16.752c0 .1748.0142.3515.0352.5273.0141.083.0844.1475.1689.1475h15.9814c.0909 0 .1758-.0645.2032-.1553l.12-.4268zm2.7568-5.5634c-.0771 0-.1611 0-.2383.0112-.0566 0-.1054.0415-.127.0976l-.3378 1.1744c-.1475.5068-.0918.9707.1543 1.3164.2256.3164.6055.498 1.0625.5195l1.8437.1133c.0557 0 .1055.0263.1329.0703.0283.043.0351.1074.0214.1562-.0283.084-.1132.1485-.204.1553l-1.921.1123c-1.041.0488-2.1582.8867-2.5527 1.914l-.1406.3585c-.0283.0713.0215.1416.0986.1416h6.5977c.0771 0 .1474-.0489.169-.126.1122-.4082.1757-.837.1757-1.2803 0-2.6025-2.125-4.727-4.7344-4.727',
  },
  {
    name: 'GitHub Pages',
    color: '#181717',
    path: 'M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12',
  },
  {
    name: 'Streamlit',
    color: '#FF4B4B',
    path: 'M16.673 11.32l6.862-3.618c.233-.136.554.12.442.387L20.463 17.1zm-8.556-.229l3.473-5.187c.203-.328.578-.316.793-.028l7.886 11.75zm-3.375 7.25c-.28 0-.835-.284-.993-.716l-3.72-9.46c-.118-.331.139-.614.48-.464l19.474 10.306c-.149.147-.453.337-.72.334z',
  },
];

const heroMetricBars = [22, 38, 30, 52, 44, 70, 58, 82, 66, 96];

function HeroGlyph({type}) {
  if (type === 'dbt') {
    return <DbtMark />;
  }
  if (type === 'declarative') {
    return <WhyGlyfIcon type="declarative" />;
  }
  if (type === 'agent') {
    return <WhyGlyfIcon type="agent" />;
  }
  if (type === 'bolt') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M13 3L5 13.5H11.5L10.5 21L19 10.5H12.5L13 3Z" />
      </svg>
    );
  }
  if (type === 'server') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="4" y="4" width="16" height="7" rx="1.5" />
        <rect x="4" y="13" width="16" height="7" rx="1.5" />
        <path d="M8 7.5H8.1M8 16.5H8.1M3 3L21 21" />
      </svg>
    );
  }
  if (type === 'chevron') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M9 6L15 12L9 18" />
      </svg>
    );
  }
  if (type === 'engine') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="7" y="7" width="10" height="10" rx="1.5" />
        <path d="M10 3V7M14 3V7M10 17V21M14 17V21M3 10H7M3 14H7M17 10H21M17 14H21" />
      </svg>
    );
  }
  if (type === 'database') {
    return <VectorIcon type="database" />;
  }
  return <WhyGlyfIcon type="code" />;
}

function HeroArrow({className}) {
  return (
    <svg className={className} viewBox="0 0 60 40" aria-hidden="true">
      <path d="M4 4C10 22 28 32 52 32" />
      <path d="M44 25L53 32L44 38" />
    </svg>
  );
}

function HeroDiagram() {
  const logoUrl = useBaseUrl('/img/glyf-logo-v4.svg');
  const hostedDashboardUrl = useBaseUrl('/dashboards/sales-dashboard/dashboards/sales.html');
  return (
    <figure className="glyfHeroDiagram" aria-label="dbt models, YAML layouts, and Python macros go through glyf build and ship as dashboards, embedded analytics, and hosted dashboards">
      <div className="glyfHeroFlow">
        <div className="glyfHeroInputs">
          {heroInputs.map((item) => (
            <div className="glyfHeroCard glyfHeroInput" key={item.title}>
              <span className={`glyfHeroIcon glyfHeroIcon--${item.icon}`}><HeroGlyph type={item.icon} /></span>
              <span className="glyfHeroCardText">
                <strong>{item.title}</strong>
                <small>{item.detail}</small>
                {item.tag ? <span className="glyfHeroTag">{item.tag}</span> : null}
              </span>
            </div>
          ))}
        </div>
        <svg className="glyfHeroWires glyfHeroWires--in" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 12.5C50 12.5 50 50 100 50M0 37.5C50 37.5 50 50 100 50M0 62.5C50 62.5 50 50 100 50M0 87.5C50 87.5 50 50 100 50" vectorEffect="non-scaling-stroke" />
        </svg>
        <div className="glyfHeroHub">
          <img src={logoUrl} alt="" width="44" height="44" />
          <strong>Glyf build</strong>
          <small>Validate · render · export</small>
        </div>
        <svg className="glyfHeroWires glyfHeroWires--out" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 50C50 50 50 26.19 100 26.19M0 50C50 50 50 64.29 100 64.29M0 50C50 50 50 88.1 100 88.1" vectorEffect="non-scaling-stroke" />
        </svg>
        <div className="glyfHeroOutputs">
          <div className="glyfHeroSlot glyfHeroSlot--tall">
            <Link className="glyfHeroCard glyfHeroOutput glyfHeroOutput--dashboards" to="/docs/examples/gallery">
              <span className="glyfHeroOutputHead">
                <span className="glyfHeroIcon"><SmallChartIcon type="bars" /></span>
                <strong>Dashboards</strong>
                <span className="glyfHeroChevron"><HeroGlyph type="chevron" /></span>
              </span>
              <span className="glyfHeroMini">
                <span className="glyfHeroMiniLabel">Revenue <span className="glyfHeroMiniBadge">Rendered</span></span>
                <svg className="glyfHeroSpark" viewBox="0 0 200 56" preserveAspectRatio="none" aria-hidden="true">
                  <path className="glyfHeroSparkArea" d="M0 46L22 40L40 44L62 30L84 36L106 24L128 26L150 12L172 22L200 16V56H0Z" />
                  <path className="glyfHeroSparkLine" d="M0 46L22 40L40 44L62 30L84 36L106 24L128 26L150 12L172 22L200 16" vectorEffect="non-scaling-stroke" />
                </svg>
              </span>
              <span className="glyfHeroMini">
                <span className="glyfHeroMiniLabel">Product metrics</span>
                <span className="glyfHeroBars" aria-hidden="true">
                  {heroMetricBars.map((height, index) => (
                    <span key={index} style={{height: `${height}%`}} className={index % 2 ? 'is-strong' : undefined} />
                  ))}
                </span>
              </span>
            </Link>
          </div>
          <div className="glyfHeroSlot">
            <Link className="glyfHeroCard glyfHeroOutput" to="/docs/integrations/embedded-analytics">
              <span className="glyfHeroIcon"><HeroGlyph type="code" /></span>
              <span className="glyfHeroCardText">
                <strong>Embedded analytics</strong>
                <small>SVG · PNG · app</small>
              </span>
              <span className="glyfHeroChevron"><HeroGlyph type="chevron" /></span>
            </Link>
          </div>
          <div className="glyfHeroSlot">
            <a className="glyfHeroCard glyfHeroOutput" href={hostedDashboardUrl}>
              <span className="glyfHeroIcon"><SmallChartIcon type="line" /></span>
              <span className="glyfHeroCardText">
                <strong>Hosted dashboards</strong>
                <small>HTML · S3 · docs</small>
              </span>
              <span className="glyfHeroChevron"><HeroGlyph type="chevron" /></span>
            </a>
          </div>
        </div>
      </div>
      <div className="glyfHeroShip">
        <p className="glyfHeroNote glyfHeroNote--bottom" aria-hidden="true">
          Ship anywhere
          <HeroArrow className="glyfHeroNoteArrow" />
        </p>
        <ul className="glyfHeroDestinations" aria-label="Static output can be published to">
          {heroDestinations.map((item) => (
            <li key={item.name} title={item.name}>
              <svg viewBox="0 0 24 24" role="img" aria-label={item.name} style={{fill: item.color}}>
                <path d={item.path} />
              </svg>
            </li>
          ))}
          <li className="glyfHeroDestinationsMore" aria-hidden="true">···</li>
        </ul>
      </div>
    </figure>
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
          <span className="featureMcpMessage featureMcpMessage--dim">→ patch revenue_weekly.ggsql</span>
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
<span className="codeKw">GROUP BY</span> <span className="codeNum">1</span>, <span className="codeNum">3</span>{'\n'}
<span className="codeMuted">────────────────────────────</span>{'\n'}
<span className="codeOk">✓</span> resolved orders → analytics.orders{'\n'}
<span className="codeOk">✓</span> resolved plans → analytics.plans{'\n'}
<span className="codeOk">✓</span> query valid — 0 errors</code></pre>
        </FeatureMacWindow>
      );
    case 'visualDiffTerminal':
      return <VisualDiffTerminal filename={item.filename} />;
    case 'visualDiffReport':
      return (
        <FeatureMacWindow filename={item.filename}>
          <img
            src="/img/visual-diff/report-card.png"
            alt="One chart from the visual diff report, shown three times: before, after, and what moved, where the new bars are drawn over the baseline's in grey and every month that moved is boxed. Above them it says bars: 12 gone (Partners), rows 48 to 36, and the sum of expenses down 8.4 percent."
            className="visualDiffReport"
            width="2208"
            height="922"
            loading="lazy"
          />
        </FeatureMacWindow>
      );
    case 'piiDeny':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeMuted"># glyf.yml</span>{'\n'}
privacy:{'\n'}
{'  '}pii_columns: [<span className="codeStr">customer_email</span>]{'\n'}
{'  '}on_pii: <span className="codeStr">deny</span>{'\n'}
<span className="codeFn">$</span> glyf build{'\n'}
<span className="codeOk">✓</span> validated project{'\n'}
<span className="featureDiffLine featureDiffLine--remove">Render failed</span>
<span className="featureDiffLine featureDiffLine--remove">  - visualisations/overdue_invoices.ggsql returns a PII column:</span>
<span className="featureDiffLine featureDiffLine--remove">    'customer_email'. Drop it from the query, or set</span>
<span className="featureDiffLine featureDiffLine--remove">    privacy.on_pii: redact to publish it masked.</span>
<span className="codeMuted"># with on_pii: redact, the build passes and the rows carry</span>{'\n'}
<span className="codeMuted">#</span> {'{'}<span className="codeStr">"customer_email"</span>: <span className="codeStr">"I***"</span>, <span className="codeStr">"amount"</span>: <span className="codeNum">16391.88</span>, <span className="codeStr">"days_to_pay"</span>: <span className="codeNum">102</span>{'}'}</code></pre>
        </FeatureMacWindow>
      );
    case 'rowDataModes':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeMuted"># one 8-chart dashboard, exported three ways</span>{'\n'}
export.row_data: <span className="codeStr">include</span>{'   '}<span className="codeMuted">finance.html  106 KB</span>{'\n'}
<span className="codeMuted">  every row behind every chart, for interaction</span>{'\n'}
export.row_data: <span className="codeStr">minimal</span>{'   '}<span className="codeMuted">finance.html  105 KB</span>{'\n'}
<span className="codeMuted">  only the columns each chart draws; bookings and</span>{'\n'}
<span className="codeMuted">  gross_margin were selected, not plotted: gone</span>{'\n'}
export.row_data: <span className="codeStr">exclude</span>{'   '}<span className="codeMuted">finance.html   26 KB</span>{'\n'}
<span className="codeMuted">  rendered images only. No rows, no specs, no SQL.</span>{'\n\n'}
<span className="codeMuted"># bundle.json records it, every build</span>{'\n'}
<span className="codeStr">"security"</span>: {'{'} <span className="codeStr">"row_data"</span>: <span className="codeStr">"excluded"</span> {'}'}</code></pre>
        </FeatureMacWindow>
      );
    case 'gitDiff':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeFn">$</span> git diff main..feat/q3-charts{'\n\n'}
<span className="featureDiffLine featureDiffLine--context">  charts/revenue_weekly.ggsql</span>
<span className="featureDiffLine featureDiffLine--remove">- GROUP BY date_trunc('week', created_at)</span>
<span className="featureDiffLine featureDiffLine--add">+ GROUP BY date_trunc('month', created_at)</span>{'\n'}
<span className="featureDiffLine featureDiffLine--context">  dashboards/growth.yaml</span>
<span className="featureDiffLine featureDiffLine--add">+ - id: new_mrr_cohort</span>
<span className="featureDiffLine featureDiffLine--add">+   sql: ./new_mrr_cohort.sql</span>
<span className="codeMuted">2 files changed, 3 insertions(+), 1 deletion(-)</span>{'\n\n'}
<span className="codeOk">✓</span> glyf build passed — 14 charts{'\n'}
<span className="codeMuted">Ready to merge.</span></code></pre>
        </FeatureMacWindow>
      );
    case 'buildOutput':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeFn">$</span> glyf build --target prod{'\n'}
<span className="codeMuted">Building 12 charts...</span>{'\n'}
<span className="codeOk">✓</span> revenue_weekly{'\n'}
<span className="codeOk">✓</span> signups_by_plan{'\n'}
<span className="codeOk">✓</span> churn_cohort{'\n'}
<span className="codeMuted">  ... 9 more</span>{'\n'}
<span className="codeMuted">Exporting static assets...</span>{'\n'}
<span className="codeOk">✓</span> dist/revenue_weekly.html <span className="codeMuted">42kb</span>{'\n'}
<span className="codeOk">✓</span> dist/signups_by_plan.html <span className="codeMuted">38kb</span>{'\n'}
<span className="codeOk">✓</span> dist/index.html <span className="codeMuted">8kb</span>{'\n'}
<span className="codeOk">✓</span> dist/charts.zip <span className="codeMuted">180kb</span>{'\n'}
<span className="codeMuted">No server required.</span>{'\n'}
<span className="codeMuted">Drop into S3, Notion, GitHub Pages, or CI artifacts.</span></code></pre>
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
{'  }'}.get(plan, <span className="codeStr">"#e2e8f0"</span>){'\n'}
<span className="codeFn">@macro</span>{'\n'}
<span className="codeKw">def</span> <span className="codeFn">alert_threshold</span>(ctx: <span className="codeVar">ChartContext</span>) -&gt; <span className="codeVar">float</span>:{'\n'}
{'  '}<span className="codeKw">return</span> ctx.config[<span className="codeStr">"alert_pct"</span>]{'\n'}
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
{'    '}visible_if: <span className="codeStr">"user.plan == \'enterprise\'"</span>{'\n'}
<span className="codeOk">✓</span> <span className="codeMuted">dashboard spec validated — 3 charts</span></code></pre>
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
    case 'reactEmbed':
      return (
        <FeatureMacWindow filename={item.filename}>
          <pre><code><span className="codeKw">import</span> {'{ '}<span className="codeFn">GlyfProvider</span>, <span className="codeFn">GlyfChart</span>{' }'} <span className="codeKw">from</span> <span className="codeStr">'@glyf/react'</span>{'\n\n'}
<span className="codeKw">export function</span> <span className="codeFn">Analytics</span>() {'{'}{'\n'}
{'  '}<span className="codeKw">return</span> ({'\n'}
{'    '}&lt;<span className="codeFn">GlyfProvider</span> bundleUrl=<span className="codeStr">"/glyf/product_analytics/bundle.json"</span>&gt;{'\n'}
{'      '}&lt;<span className="codeFn">GlyfChart</span> name=<span className="codeStr">"activation_by_plan"</span> artifact=<span className="codeStr">"svg"</span> /&gt;{'\n'}
{'      '}&lt;<span className="codeFn">GlyfChart</span> name=<span className="codeStr">"revenue_weekly"</span> showTitle /&gt;{'\n'}
{'    '}&lt;/<span className="codeFn">GlyfProvider</span>&gt;{'\n'}
{'  '}){'\n'}
{'}'}{'\n\n'}
<span className="codeOk">✓</span> <span className="codeMuted">reads bundle.json · renders SVG or PNG · no BI SDK</span></code></pre>
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
    <header className="glyfHero">
      <div className="container glyfHero__inner">
        <div className="glyfHero__copy">
          <p className="glyfHero__badge">Open source</p>
          <h1 className="glyfHero__title">
            Build visualizations <span>the way you build pipelines</span>
          </h1>
          <p className="glyfHero__lead">
            Glyf is an open source, code-first build step for defining, testing, and shipping
            charts and dashboards from your dbt models.
          </p>
          <div className="glyfHero__actions">
            <Link className="glyfHero__button glyfHero__button--primary" to="/docs/get-started/quickstart">
              <span aria-hidden="true">&gt;_</span> Get Started <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
          <ul className="glyfHero__traits">
            {heroTraits.map(([icon, label]) => (
              <li key={label}><HeroGlyph type={icon} />{label}</li>
            ))}
          </ul>
        </div>
        <HeroDiagram />
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
            Glyf turns visualization into a build step engineers can validate, review, and ship
            with the rest of the data pipeline.
            Charts and dashboards stay inside the engineering workflow instead of drifting into
            disconnected BI tools.
          </p>
        </div>
        <div className="featureIntroSignals" aria-label="Glyf platform highlights">
          <div className="featureIntroSignal">
            <span className="featureIntroSignalMark" aria-hidden="true">
              ✓
            </span>
            <span>Broken refs and missing charts fail validation before anything ships.</span>
          </div>
          <div className="featureIntroSignal">
            <span className="featureIntroSignalMark" aria-hidden="true">
              ✓
            </span>
            <span>A chart that returns personal data fails the build; a published site carries only the rows you chose.</span>
          </div>
          <div className="featureIntroSignal">
            <span className="featureIntroSignalMark" aria-hidden="true">
              ✓
            </span>
            <span>Integrated with dbt and GGSQL today. SQLMesh and more on the roadmap.</span>
          </div>
        </div>
        <div className="featureStoryNavBand">
          <div className="featureStoryNav" role="navigation" aria-label="Feature section anchors">
            <div className="featureStoryNavLinks">
              {featureSections.map((section) => (
                <a
                  className={`featureStoryNavLink${section.id === activeFeatureSection ? ' is-active' : ''}`}
                  href={`#${section.id}`}
                  key={section.id}
                  onClick={() => setActiveFeatureSection(section.id)}
                >
                  {section.label}
                </a>
              ))}
            </div>
          </div>
        </div>
        <div className="featureStories">
          {featureSections.map((section) => (
            <article className="featureStorySection" data-feature-anchor id={section.id} key={section.id}>
              <div className="featureStoryHeader">
                <div className="featureStoryTag">{section.tag}</div>
                <h3>{section.title}</h3>
                <p>{section.description}</p>
              </div>
              <div className="featureStoryBlocks">
                {section.items.map((item) => (
                  <div className="featureStoryBlock" key={`${section.id}-${item.name}`}>
                    <div className="featureStoryVisual">
                      <FeatureVisual item={item} />
                    </div>
                    <div className="featureStoryNote">
                      <div className="featureStoryName">
                        <span>{item.name}</span>
                        {item.status === 'soon' ? (
                          <span className="featureStatus">Coming soon</span>
                        ) : null}
                        {item.status === 'preview' ? (
                          <span className="featureStatus">Preview</span>
                        ) : null}
                      </div>
                      <p className="featureStoryDesc">{item.desc}</p>
                      {item.links ? (
                        <p className="featureStoryLinks">
                          {item.links.map(([label, href]) => (
                            <Link key={href} to={href}>
                              {label}
                            </Link>
                          ))}
                        </p>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
        <div className="featureRoadmap">
          <div className="featureRoadmapHead">
            <p className="eyebrow">Roadmap</p>
            <a className="featureRoadmapButton featureRoadmapButton--secondary" href={roadmapIssuesUrl}>
              View roadmap <span aria-hidden="true">&rarr;</span>
            </a>
          </div>
          <ul className="featureRoadmapList">
            {roadmapItems.map(([title, description, issueUrl]) => (
              <li key={title}>
                <strong>{title}</strong>
                <p>{description}</p>
                <a className="featureRoadmapLink" href={issueUrl}>
                  Discuss on GitHub <span aria-hidden="true">↗</span>
                </a>
              </li>
            ))}
          </ul>
          <div className="featureRoadmapAsk">
            <span className="featureRoadmapAskIcon" aria-hidden="true"><SparkleIcon /></span>
            <div className="featureRoadmapAskText">
              <strong>Missing something?</strong>
              <p>Describe the chart or workflow you need. Feature requests land on the public roadmap, where anyone can add a 👍.</p>
            </div>
            <a className="featureRoadmapButton featureRoadmapButton--primary" href={featureRequestUrl}>
              Request a feature
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

const walkthroughChapters = [
  {start: 0, title: 'dbt model'},
  {start: 6, title: 'GGSQL chart'},
  {start: 13, title: 'Dashboard YAML'},
  {start: 20, title: 'Build'},
  {start: 28, title: 'Rendered dashboard'},
];

function walkthroughTime(seconds) {
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
}

function HowItWorks() {
  const walkthroughUrl = useBaseUrl('/assets/walkthrough/glyf-sales-walkthrough.mp4');
  const walkthroughPoster = useBaseUrl('/assets/walkthrough/poster.png');
  const videoRef = React.useRef(null);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(42);
  const [playing, setPlaying] = React.useState(false);
  const activeChapter = walkthroughChapters.reduce(
    (active, chapter, index) => currentTime >= chapter.start ? index : active, 0,
  );

  function jumpToChapter(start) {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = start;
    setCurrentTime(start);
    video.play().catch(() => {});
  }

  return (
    <section className="howSection">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">how it works</p>
          <h2>Charts, dashboards, and outputs in one build step.</h2>
          <p>
            Glyf keeps authoring close to the project: charts in GGSQL and its Glyf extensions, dashboard composition
            in YAML, reusable logic in Python, and outputs from the CLI.
          </p>
        </div>
        <figure className="howWalkthrough">
          <div className="howWalkthroughFrame">
            <video
              ref={videoRef}
              className="howWalkthroughVideo"
              onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
              onPlay={() => setPlaying(true)}
              onEnded={() => setPlaying(false)}
              onLoadedMetadata={(event) => {
                const value = event.currentTarget.duration;
                if (Number.isFinite(value) && value > 28) setDuration(value);
              }}
              controls
              playsInline
              preload="metadata"
              poster={walkthroughPoster}
              width="1600"
              height="940"
              aria-label="Sales dashboard walkthrough: from a dbt model to a rendered dashboard"
            >
              <source src={walkthroughUrl} type="video/mp4" />
              <a href={walkthroughUrl}>Watch the sales dashboard walkthrough.</a>
            </video>
            {playing ? null : (
              <button
                type="button"
                className="howWalkthroughPlay"
                onClick={() => videoRef.current?.play().catch(() => {})}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M8 5.5V18.5L18.5 12L8 5.5Z" />
                </svg>
                View Demo
                <span className="howWalkthroughPlayTime">{walkthroughTime(duration)}</span>
              </button>
            )}
          </div>
          <nav className="howChapterTimeline" aria-label="Walkthrough chapters">
            {walkthroughChapters.map((chapter, index) => {
              const end = walkthroughChapters[index + 1]?.start ?? duration;
              const progress = Math.max(0, Math.min(1, (currentTime - chapter.start) / (end - chapter.start)));
              return (
                <button
                  type="button"
                  key={chapter.start}
                  className="howChapter"
                  style={{flexGrow: end - chapter.start, '--chapter-progress': `${progress * 100}%`}}
                  aria-label={`${chapter.title}, jump to ${walkthroughTime(chapter.start)}`}
                  aria-current={index === activeChapter ? 'step' : undefined}
                  onClick={() => jumpToChapter(chapter.start)}
                >
                  <span className="howChapterTrack" />
                  <span className="howChapterTooltip">{walkthroughTime(chapter.start)} · {chapter.title}</span>
                </button>
              );
            })}
          </nav>
          <figcaption className="howChapterCaption">
            <span>{walkthroughTime(currentTime)} / {walkthroughTime(duration)} · {walkthroughChapters[activeChapter].title}</span>
            <span>Choose a chapter to jump ahead</span>
          </figcaption>
        </figure>
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
  const personaIcons = [
    <VectorIcon type="database" />,
    <VectorIcon type="notebook" />,
    <SmallChartIcon type="line" />,
    <VectorIcon type="component" />,
  ];
  return (
    <section className="personasSection">
      <div className="container">
        <div className="sectionHeader">
          <p className="eyebrow">who it's for</p>
          <h2>Built for everyone who touches data.</h2>
        </div>
        <div className="personasGrid">
          {personas.map(([role, title, description], index) => (
            <article className="personaCard" key={role}>
              <div className="personaIcon" aria-hidden="true">{personaIcons[index]}</div>
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

// Real output. One filter was added to a model of examples/finance_metrics, both
// branches were built, and this is what `glyf diff` printed. [kind, text, pause in ms]
const visualDiffSession = [
  ['cmd', 'git diff main -- models/fct_finance.sql', 500],
  ['ctx', " from {{ source('raw', 'finance') }}", 60],
  ['add', "+where department != 'Partners'", 60],
  ['ctx', ' group by 1, 2', 700],
  ['cmd', 'glyf diff --baseline ../base', 600],
  ['chart', '~ bookings_trend: 6.1% of the picture moved (the rows changed)', 130],
  ['marks', '    points: 12 lower', 90],
  ['row', '    sum of bookings 1,079,700 → 974,000 (-9.8%)', 130],
  ['chart', '~ expenses_by_department: 50.8% of the picture moved (the rows changed)', 130],
  ['marks', '    bars: 12 gone (Partners)', 90],
  ['row', '    rows 48 → 36', 90],
  ['row', '    gone from department: Partners', 90],
  ['row', '    sum of expenses 576,000 → 527,500 (-8.4%)', 130],
  ['chart', '~ gross_margin_trend: 7.4% of the picture moved (the rows changed)', 130],
  ['marks', '    points: 12 lower', 90],
  ['row', '    sum of gross_margin 503,700 → 446,500 (-11.4%)', 130],
  ['chart', '~ margin_rate_by_department: 35.0% of the picture moved (the rows changed)', 130],
  ['row', '    rows 48 → 36', 90],
  ['row', '    gone from department: Partners', 130],
  ['chart', '~ margin_share: 31.3% of the picture moved (the rows changed)', 130],
  ['row', '    rows 4 → 3', 90],
  ['row', '    gone from department: Partners', 90],
  ['row', '    sum of gross_margin 503,700 → 446,500 (-11.4%)', 130],
  ['chart', '~ margin_vs_expenses: 0.9% of the picture moved (the rows changed)', 130],
  ['row', '    rows 48 → 36', 90],
  ['row', '    gone from department: Partners', 300],
  ['ok', '✓ 6 changed, 2 unchanged', 200],
  ['ok', '✓ wrote target/glyf/diff/index.html', 0],
];

function VisualDiffTerminal({filename}) {
  const total = visualDiffSession.length;
  // Everything is shown until the script runs, so the page reads the same
  // without JavaScript and for anyone who has asked for less motion.
  const [shown, setShown] = React.useState(total);
  const [playing, setPlaying] = React.useState(false);
  const rootRef = React.useRef(null);
  const bodyRef = React.useRef(null);
  const startedRef = React.useRef(false);

  const play = () => {
    setShown(0);
    setPlaying(true);
  };

  React.useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return undefined;
    }
    setShown(0);
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !startedRef.current) {
          startedRef.current = true;
          setPlaying(true);
        }
      },
      {threshold: 0.35},
    );
    observer.observe(rootRef.current);
    return () => observer.disconnect();
  }, []);

  React.useEffect(() => {
    if (!playing) {
      return undefined;
    }
    if (shown >= total) {
      setPlaying(false);
      return undefined;
    }
    const pause = shown === 0 ? 300 : visualDiffSession[shown - 1][2];
    const timer = window.setTimeout(() => setShown((count) => count + 1), pause);
    return () => window.clearTimeout(timer);
  }, [playing, shown, total]);

  React.useEffect(() => {
    // Follow the output the way a terminal does.
    const body = bodyRef.current;
    if (body) {
      body.scrollTop = body.scrollHeight;
    }
  }, [shown]);

  return (
    <div className="visualDiffTerminal" ref={rootRef}>
      <div className="featureMacWindow">
        <div className="featureMacTitlebar">
          <span className="featureMacDot featureMacDot--red" />
          <span className="featureMacDot featureMacDot--yellow" />
          <span className="featureMacDot featureMacDot--green" />
          <span className="featureMacFilename">{filename}</span>
          {/* In the title bar, so it never sits on top of the output. */}
          <button
            type="button"
            className="visualDiffTerminal__replay"
            onClick={play}
            disabled={playing}
          >
            Replay
          </button>
        </div>
        <div className="visualDiffTerminal__body" ref={bodyRef} aria-hidden="true">
          <pre>
            <code>
              {visualDiffSession.slice(0, shown).map(([kind, text], index) => (
                <span className={`visualDiffLine visualDiffLine--${kind}`} key={index}>
                  {kind === 'cmd' ? <span className="codeFn">$ </span> : null}
                  {text}
                  {'\n'}
                </span>
              ))}
              {shown < total ? <span className="visualDiffCursor" /> : null}
            </code>
          </pre>
        </div>
        {/* The same session for a screen reader, which should not be read a
            terminal one line at a time. */}
        <pre className="visualDiffTerminal__transcript">
          {visualDiffSession.map(([kind, text]) => `${kind === 'cmd' ? '$ ' : ''}${text}`).join('\n')}
        </pre>
      </div>
    </div>
  );
}

function CtaSection() {
  return (
    <section className="ctaBand">
      <div className="container ctaBand__inner">
        <h2>Turn your dbt project into dashboards.</h2>
        <p>Install glyf, point it at your dbt project, and build your first dashboard.</p>
        <div className="ctaBand__install">
          <span aria-hidden="true">$</span>
          <code>uv tool install glyf-core</code>
        </div>
        <div className="ctaBand__actions">
          <Link className="ctaBand__button ctaBand__button--primary" to="/docs/get-started/quickstart">
            <span aria-hidden="true">&gt;_</span> Get Started <span aria-hidden="true">&rarr;</span>
          </Link>
          <a className="ctaBand__button ctaBand__button--secondary" href="https://github.com/glyf-data/glyf">
            View on GitHub
          </a>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout
      title="Build visualizations the way you build pipelines"
      description="Glyf is an open source, code-first build step for defining, testing, and shipping charts and dashboards from your dbt models."
    >
      <HomepageHeader />
      <main className="landingSections">
        <HowItWorks />
        <FeaturesSection />
        <PersonasSection />
        <CtaSection />
      </main>
    </Layout>
  );
}
