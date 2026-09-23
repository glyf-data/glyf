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
          {to: '/docs/examples/gallery', label: 'Examples', position: 'left'},
          {to: '/docs/integrations/overview', label: 'Integrations', position: 'left'},
          {to: '/docs/resources/roadmap', label: 'Roadmap', position: 'left'},
          {to: '/docs/resources/support', label: 'Support', position: 'left'},
          {
            type: 'html',
            position: 'right',
            value:
              '<a class="navbarSlackLink" href="/slack" aria-label="Join the glyf community on Slack"><svg class="navbarSlackMark" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M5.04 15.16a2.52 2.52 0 1 1-2.52-2.52h2.52v2.52Zm1.27 0a2.52 2.52 0 0 1 5.04 0v6.32a2.52 2.52 0 1 1-5.04 0v-6.32ZM8.83 5.04a2.52 2.52 0 1 1 2.52-2.52v2.52H8.83Zm0 1.27a2.52 2.52 0 0 1 0 5.04H2.52a2.52 2.52 0 1 1 0-5.04h6.31Zm10.13 2.52a2.52 2.52 0 1 1 2.52 2.52h-2.52V8.83Zm-1.27 0a2.52 2.52 0 0 1-5.04 0V2.52a2.52 2.52 0 1 1 5.04 0v6.31Zm-2.52 10.13a2.52 2.52 0 1 1-2.52 2.52v-2.52h2.52Zm0-1.27a2.52 2.52 0 0 1 0-5.04h6.32a2.52 2.52 0 1 1 0 5.04h-6.32Z"/></svg><span>Join Slack Community</span></a>',
          },
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
              {label: 'Slack', href: 'https://glyfdata.com/slack'},
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
