const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

const siteUrl = (process.env.DOCS_SITE_URL || 'https://glyf.pages.dev').replace(/\/$/, '');
const rawBaseUrl = process.env.DOCS_SITE_BASE_URL || '/';
const normalizedBaseUrl = rawBaseUrl.startsWith('/') ? rawBaseUrl : `/${rawBaseUrl}`;
const baseUrl = normalizedBaseUrl.endsWith('/') ? normalizedBaseUrl : `${normalizedBaseUrl}/`;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'glyf',
  tagline: 'Visualization belongs in the pipeline',
  favicon: 'img/favicon-v2.svg',

  url: siteUrl,
  baseUrl,

  organizationName: 'kannandreams',
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
          editUrl: 'https://github.com/kannandreams/glyf/edit/main/docs-site/',
          routeBasePath: 'docs',
        },
        blog: {
          routeBasePath: 'blog',
          blogTitle: 'Glyf Blog',
          blogDescription: 'Notes on dbt-aware visualization, static dashboard builds, and analytics engineering workflows.',
          showReadingTime: true,
          postsPerPage: 9,
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/glyf-logo-v4.svg',
      colorMode: {
        defaultMode: 'light',
        disableSwitch: true,
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
          {
            type: 'dropdown',
            label: 'Resources',
            position: 'left',
            items: [
              {to: '/blog', label: 'Blog'},
              {to: '/docs/resources/roadmap', label: 'Roadmap'},
              {to: '/docs/resources/community', label: 'Community'},
              {
                href: 'https://github.com/kannandreams/glyf/blob/main/CONTRIBUTING.md',
                label: 'Contributing',
              },
            ],
          },
          {
            type: 'html',
            position: 'right',
            value:
              '<a class="navbarGithubLink" href="https://github.com/kannandreams/glyf" aria-label="Open Glyf on GitHub"><span>GitHub</span><svg class="navbarExternalIcon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7H17V17" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 7L6 18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg><span class="navbarVersionTag">v0.1-alpha</span></a>',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {label: 'GitHub', href: 'https://github.com/kannandreams/glyf'},
          {label: 'Docs', to: '/docs/intro'},
          {label: 'Roadmap', to: '/docs/resources/roadmap'},
          {label: 'Apache License', href: 'https://github.com/kannandreams/glyf/blob/main/LICENSE'},
        ],
        copyright: '<strong class="footerBrand">Glyf<span>.</span></strong><span class="footerTagline">Visualization is a build step. Treat it like one.</span>',
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['bash', 'sql', 'yaml'],
      },
    }),
};

module.exports = config;
