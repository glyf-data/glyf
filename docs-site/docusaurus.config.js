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
  favicon: 'img/glyf-mark.svg',

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
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/glyf-mark.svg',
      colorMode: {
        defaultMode: 'light',
        disableSwitch: true,
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'Glyf',
        logo: {
          alt: 'Glyf mark',
          src: 'img/glyf-mark.svg',
        },
        items: [
          {to: '/docs/intro', label: 'Docs', position: 'left'},
          {to: '/docs/examples/gallery', label: 'Examples', position: 'left'},
          {to: '/docs/integrations/overview', label: 'Integrations', position: 'left'},
          {
            type: 'dropdown',
            label: 'Community',
            position: 'left',
            items: [
              {to: '/docs/resources/community', label: 'Community'},
              {to: '/docs/resources/roadmap', label: 'Roadmap'},
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
              '<a class="navbarGithubLink" href="https://github.com/kannandreams/glyf" aria-label="Glyf on GitHub"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .5A11.5 11.5 0 0 0 .5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2.02c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.19-3.08-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18a10.95 10.95 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.11 3.04.74.8 1.19 1.82 1.19 3.08 0 4.42-2.69 5.39-5.25 5.68.41.35.78 1.05.78 2.12v3.14c0 .31.21.68.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5Z"/></svg><span>GitHub</span><svg class="navbarExternalIcon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7H17V17" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 7L6 18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></a>',
          },
          {
            type: 'html',
            position: 'right',
            value:
              '<a class="navbarStarGroup" href="https://github.com/kannandreams/glyf" aria-label="Star Glyf on GitHub"><span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2L14.7 8.6L20.6 9.5L16.3 13.7L17.3 19.6L12 16.8L6.7 19.6L7.7 13.7L3.4 9.5L9.3 8.6L12 3.2Z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/></svg>Star</span><strong>1.2k</strong></a>',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {label: 'GitHub', href: 'https://github.com/kannandreams/glyf'},
          {label: 'Docs', to: '/docs/intro'},
          {label: 'Roadmap', to: '/docs/resources/roadmap'},
          {label: 'MIT License', href: 'https://github.com/kannandreams/glyf/blob/main/LICENSE'},
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
