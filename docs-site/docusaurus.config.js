const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'dbt-charts',
  tagline: 'A lightweight dashboard layer for analytics engineers',
  favicon: 'img/dbt-charts-mark.svg',

  url: 'https://kannandreams.github.io',
  baseUrl: '/dbt-charts/',

  organizationName: 'kannandreams',
  projectName: 'dbt-charts',

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
          editUrl: 'https://github.com/kannandreams/dbt-charts/edit/main/docs-site/',
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
      image: 'img/dbt-charts-mark.svg',
      announcementBar: {
        id: 'release-preview',
        content:
          'Docs preview for dbt-charts 0.1.0: quickstart, examples gallery, AI context, and migration placeholders are now in progress.',
        backgroundColor: '#07130f',
        textColor: '#ffffff',
        isCloseable: true,
      },
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'dbt-charts',
        logo: {
          alt: 'dbt-charts mark',
          src: 'img/dbt-charts-mark.svg',
        },
        items: [
          {to: '/docs/intro', label: 'Docs', position: 'left'},
          {to: '/docs/examples/gallery', label: 'Examples', position: 'left'},
          {to: '/docs/reference/cli', label: 'CLI', position: 'left'},
          {to: '/docs/ai-context/overview', label: 'AI Context', position: 'left'},
          {to: '/docs/ai-context/agents', label: 'Agents', position: 'left'},
          {to: '/docs/integrations/overview', label: 'Integrations', position: 'left'},
          {
            href: 'https://github.com/kannandreams/dbt-charts',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'light',
        links: [
          {
            title: 'Start',
            items: [
              {label: 'Quickstart', to: '/docs/get-started/quickstart'},
              {label: 'Existing dbt project', to: '/docs/get-started/existing-dbt-project'},
              {label: 'Examples gallery', to: '/docs/examples/gallery'},
            ],
          },
          {
            title: 'Build',
            items: [
              {label: 'Visualisation syntax', to: '/docs/guides/visualisation-syntax'},
              {label: 'Dashboard YAML', to: '/docs/guides/dashboard-yaml'},
              {label: 'CLI reference', to: '/docs/reference/cli'},
            ],
          },
          {
            title: 'Project',
            items: [
              {label: 'Community', to: '/docs/resources/community'},
              {label: 'Roadmap', to: '/docs/resources/roadmap'},
              {label: 'GitHub', href: 'https://github.com/kannandreams/dbt-charts'},
            ],
          },
        ],
        copyright: `Copyright ${new Date().getFullYear()} dbt-charts contributors. Released under the MIT License.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['bash', 'sql', 'yaml'],
      },
    }),
};

module.exports = config;
