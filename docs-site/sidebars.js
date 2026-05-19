/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Get Started',
      collapsed: false,
      items: [
        'get-started/quickstart',
        'get-started/existing-dbt-project',
        'get-started/project-structure',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      collapsed: false,
      items: [
        'guides/visualisation-syntax',
        'guides/dashboard-yaml',
        'guides/dbt-integration',
        'guides/configuration',
        'guides/technical-architecture',
        'guides/ci-cd',
      ],
    },
    {
      type: 'category',
      label: 'Examples Gallery',
      collapsed: false,
      items: [
        'examples/gallery',
        'examples/screenshots',
        'examples/simple-dbt',
        'examples/sales-dashboard',
        'examples/product-analytics',
        'examples/finance-metrics',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: false,
      items: ['reference/cli', 'reference/configuration'],
    },
    {
      type: 'category',
      label: 'Integrations',
      collapsed: false,
      items: [
        'integrations/overview',
        'integrations/cloudflare-pages',
        'integrations/private-access',
        'integrations/github-actions',
        'integrations/static-hosting',
      ],
    },
    {
      type: 'category',
      label: 'AI Context',
      collapsed: false,
      items: ['ai-context/overview', 'ai-context/agents', 'ai-context/assistant-setup'],
    },
    {
      type: 'category',
      label: 'Migrations',
      collapsed: false,
      items: ['migrations/looker'],
    },
    {
      type: 'category',
      label: 'Resources',
      collapsed: false,
      items: ['resources/community', 'resources/roadmap', 'resources/seo-preview', 'resources/troubleshooting'],
    },
  ],
};

module.exports = sidebars;
