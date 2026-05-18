# Private Access

The hosted documentation site should stay private during the early project phase.

Use Cloudflare Access with GitHub login and an allow policy for a single email address.

## Intended access model

| Surface | Access |
| --- | --- |
| Production docs | Private behind Cloudflare Access |
| Preview deployments | Private behind Cloudflare Access if enabled later |
| Source repository | Private GitHub repository |
| Login method | GitHub |
| Allowed users | One email address managed in Cloudflare |

## Configure GitHub login

In Cloudflare Zero Trust:

1. Go to `Settings > Authentication`.
2. Add GitHub as an identity provider.
3. Create a GitHub OAuth app when Cloudflare prompts for one.
4. Use your Cloudflare team domain as the OAuth app homepage.
5. Use the Cloudflare Access callback URL shown in the Cloudflare setup screen.
6. Save the GitHub client ID and client secret in Cloudflare.
7. Test the GitHub identity provider from Cloudflare.

## Protect preview deployments

If preview deployments are enabled later:

1. Go to `Workers & Pages`.
2. Select the `dbtcharts` Pages project.
3. Open `Settings > General`.
4. Select `Enable access policy`.
5. Configure an Allow policy for your email address.

Cloudflare protects preview deployment URLs separately from the production `*.pages.dev` URL.

## Protect production pages.dev

For the production URL:

```text
https://dbtcharts.pages.dev
```

Cloudflare currently requires an extra Access configuration step:

1. Enable the Pages access policy for preview deployments.
2. Select `Manage` on the generated Access policy.
3. Open the Access application for the Pages project.
4. Select `Configure`.
5. Under `Public hostname`, remove the wildcard subdomain.
6. Save the application.
7. Return to the Pages project and enable the preview access policy again if needed.
8. Confirm that there is one Access application for `dbtcharts.pages.dev` and one for preview URLs.

## Later custom domain

When `docs.dbtcharts.com` is added, create a separate self-hosted Access application for that hostname.

Use the same GitHub login method and email allow policy.

## Verification checklist

- Visit `https://dbtcharts.pages.dev` in a private browser window.
- Confirm Cloudflare Access appears before the docs load.
- Sign in with GitHub.
- Confirm only the configured email address can proceed.
- Confirm unauthenticated requests do not show the Docusaurus page.
