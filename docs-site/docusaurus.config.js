const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

const siteUrl = (process.env.DOCS_SITE_URL || 'https://glyf.pages.dev').replace(/\/$/, '');
const rawBaseUrl = process.env.DOCS_SITE_BASE_URL || '/';
const normalizedBaseUrl = rawBaseUrl.startsWith('/') ? rawBaseUrl : `/${rawBaseUrl}`;
const baseUrl = normalizedBaseUrl.endsWith('/') ? normalizedBaseUrl : `${normalizedBaseUrl}/`;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'glyf',
  tagline: 'Open Source Visualization build tool to data pipeline',
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
      announcementBar: {
        id: 'glyf-studio',
        content:
          '<a class="studioAnnouncementLink" href="https://glyfdata.com" aria-label="Introducing Glyf Studio">Introducing Glyf Studio <span aria-hidden="true">→</span></a>',
        backgroundColor: '#0047ff',
        textColor: '#ffffff',
        isCloseable: false,
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
              {to: '/docs/resources/roadmap', label: 'Roadmap'},
              {to: '/docs/resources/community', label: 'Community'},
              {
                href: 'https://github.com/kannandreams/glyf/blob/main/CONTRIBUTING.md',
                label: 'Contributing',
              },
            ],
          },
          {to: '/blog', label: 'Blog', position: 'left'},
          {
            href: 'https://github.com/kannandreams/glyf/blob/main/CHANGELOG.md',
            label: 'Changelog',
            position: 'right',
          },
          {
            type: 'html',
            position: 'right',
            value:
              '<a class="navbarGithubLink" href="https://github.com/kannandreams/glyf" aria-label="View Glyf on GitHub"><svg class="navbarGithubMark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.9.58.11.79-.25.79-.56 0-.28-.01-1.2-.02-2.18-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.71.08-.71 1.15.08 1.76 1.18 1.76 1.18 1.03 1.75 2.69 1.25 3.34.96.1-.74.4-1.25.73-1.54-2.55-.29-5.23-1.28-5.23-5.68 0-1.25.45-2.27 1.17-3.07-.12-.29-.51-1.46.11-3.04 0 0 .96-.31 3.14 1.17a10.9 10.9 0 0 1 5.72 0c2.18-1.48 3.14-1.17 3.14-1.17.62 1.58.23 2.75.11 3.04.73.8 1.17 1.82 1.17 3.07 0 4.41-2.69 5.39-5.26 5.67.41.35.78 1.05.78 2.12 0 1.53-.01 2.76-.01 3.13 0 .31.21.68.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" fill="currentColor"/></svg><span>View on GitHub</span></a>',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
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
