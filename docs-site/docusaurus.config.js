const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

const siteUrl = (process.env.DOCS_SITE_URL || 'https://glyfdata.com').replace(/\/$/, '');
const rawBaseUrl = process.env.DOCS_SITE_BASE_URL || '/';
const normalizedBaseUrl = rawBaseUrl.startsWith('/') ? rawBaseUrl : `/${rawBaseUrl}`;
const baseUrl = normalizedBaseUrl.endsWith('/') ? normalizedBaseUrl : `${normalizedBaseUrl}/`;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'glyf',
  tagline: 'Build visualizations the way you build pipelines',
  favicon: 'img/favicon-v2.svg',

  url: siteUrl,
  baseUrl,

  organizationName: 'glyf-data',
  projectName: 'glyf',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/glyf-data/glyf/edit/main/docs-site/',
          routeBasePath: 'docs',
        },
        blog: false,
        theme: {
          customCss: [
            require.resolve('./src/css/custom.css'),
            require.resolve('./src/css/docs.css'),
            require.resolve('./src/css/sidebar-icons.css'),
            require.resolve('./src/css/landing-light.css'),
          ],
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/glyf-social-card.png',
      metadata: [
        {name: 'twitter:card', content: 'summary_large_image'},
        {property: 'og:type', content: 'website'},
        {property: 'og:site_name', content: 'Glyf'},
        {property: 'og:image:type', content: 'image/png'},
        {property: 'og:image:width', content: '1200'},
        {property: 'og:image:height', content: '630'},
        {property: 'og:image:alt', content: 'Glyf: build visualizations the way you build pipelines'},
      ],
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'Glyf',
        logo: {
          alt: 'Glyf mark',
          src: 'img/glyf-logo-v4.svg',
        },
        items: [
          {to: '/docs/intro', label: 'Docs', position: 'left'},
          {to: '/docs/charts', label: 'Charts', position: 'left', activeBaseRegex: '^/docs/charts'},
          {to: '/docs/examples/gallery', label: 'Examples', position: 'left'},
          // A section of the home page, not a page: never shown as the current one.
          {to: '/#embed', label: 'Embed', position: 'left', activeBaseRegex: '^/embed$'},
          {to: '/docs/integrations/overview', label: 'Integrations', position: 'left'},
          {to: '/docs/resources/roadmap', label: 'Roadmap', position: 'left'},
          {to: '/docs/resources/support', label: 'Support', position: 'left'},
          {
            type: 'html',
            position: 'right',
            value:
              '<a class="navbarGithubLink navbarStar" href="https://github.com/glyf-data/glyf" aria-label="Star Glyf on GitHub"><svg class="navbarStarMark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.4l-5.9 3.2 1.3-6.6-4.9-4.6 6.6-.8z"/></svg><span>Star on GitHub</span></a>',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Product',
            items: [
              {label: 'Visual diff', to: '/docs/guides/visual-diff'},
              {label: 'Data protection', to: '/docs/guides/data-exposure'},
              {label: 'Lineage', to: '/docs/guides/dbt-integration#lineage-on-the-dashboard'},
              {label: 'MCP server', to: '/docs/integrations/mcp'},
              {label: 'Chart types', to: '/docs/guides/visualisation-syntax'},
              {label: 'Dashboards', to: '/docs/guides/dashboard-yaml'},
            ],
          },
          {
            title: 'Learn',
            items: [
              {label: 'Installation', to: '/docs/get-started/installation'},
              {label: 'Quickstart', to: '/docs/get-started/quickstart'},
              {label: 'CLI reference', to: '/docs/reference/cli'},
              {label: 'Configuration', to: '/docs/reference/configuration'},
              {label: 'Examples', to: '/docs/examples/gallery'},
              {label: 'Roadmap', to: '/docs/resources/roadmap'},
            ],
          },
          {
            title: 'Community',
            items: [
              {label: 'GitHub', href: 'https://github.com/glyf-data/glyf'},
              {label: 'Discussions', href: 'https://github.com/glyf-data/glyf/discussions'},
              {label: 'Contributing', href: 'https://github.com/glyf-data/glyf/blob/main/CONTRIBUTING.md'},
              {label: 'Support', to: '/docs/resources/support'},
              {label: 'Security', href: 'https://github.com/glyf-data/glyf/blob/main/SECURITY.md'},
              {label: 'Apache License', href: 'https://github.com/glyf-data/glyf/blob/main/LICENSE'},
            ],
          },
        ],
        copyright: '<span class="footerMark" aria-hidden="true">Glyf</span><span class="footerMeta"><span class="footerTagline">Visualization is a build step. Treat it like one.</span><span class="footerLicence">Apache-2.0 · glyf-data</span></span>',
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['bash', 'sql', 'yaml'],
      },
    }),
};

module.exports = config;
