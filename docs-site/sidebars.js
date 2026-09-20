/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */

// A page and its icon. The icon is a class; src/css/sidebar-icons.css draws it.
const doc = (id, icon) => ({type: 'doc', id, className: `sidebarIcon sidebarIcon--${icon}`});

// A group is a label over its pages, not a folder to open: the whole map is
// visible at once, which is the point of a sidebar this size.
const group = (label, items) => ({type: 'category', label, collapsible: false, items});

const sidebars = {
  docsSidebar: [
    doc('intro', 'home'),
    group('Get Started', [
      doc('get-started/installation', 'download'),
      doc('get-started/quickstart', 'zap'),
      doc('get-started/project-structure', 'folder'),
    ]),
    group('Guides', [
      doc('guides/visualisation-syntax', 'chart'),
      doc('guides/dashboard-yaml', 'layout'),
      doc('guides/dashboard-macros', 'code'),
      doc('guides/dbt-integration', 'database'),
      doc('guides/data-exposure', 'shield'),
      doc('guides/where-to-run-builds', 'server'),
      doc('guides/ci-cd', 'branch'),
      doc('guides/visual-diff', 'eye'),
    ]),
    group('Examples', [
      doc('examples/gallery', 'grid'),
      doc('examples/simple-dbt', 'box'),
      doc('examples/sales-dashboard', 'trending'),
      doc('examples/product-analytics', 'activity'),
      doc('examples/finance-metrics', 'dollar'),
    ]),
    group('Reference', [
      doc('reference/cli', 'terminal'),
      doc('reference/configuration', 'sliders'),
      doc('reference/bundle', 'file-code'),
    ]),
    group('Integrations', [
      doc('integrations/overview', 'plug'),
      doc('integrations/github-actions', 'play'),
      doc('integrations/static-hosting', 'globe'),
      doc('integrations/embedded-analytics', 'embed'),
    ]),
    group('AI Context', [
      doc('ai-context/overview', 'sparkles'),
    ]),
    group('Migrations', [
      doc('migrations/looker', 'swap'),
    ]),
    group('Resources', [
      doc('resources/support', 'lifebuoy'),
      doc('resources/troubleshooting', 'alert'),
      doc('resources/community', 'users'),
      doc('resources/roadmap', 'map'),
    ]),
  ],
};

module.exports = sidebars;
