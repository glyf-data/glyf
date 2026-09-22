// The site is glyfdata.com. Cloudflare Pages also serves it at the project's
// default hostname, glyf.pages.dev, and never redirects that itself, so a
// visitor who arrives there would share and bookmark the wrong domain.
//
// Only the bare production hostname is redirected. A preview deployment's own
// hostname (<hash>.glyf.pages.dev) is left alone, so a deploy can be checked
// at its own URL before the domain points at it.
export async function onRequest({request, next}) {
  const url = new URL(request.url);
  if (url.hostname === 'glyf.pages.dev') {
    url.protocol = 'https:';
    url.hostname = 'glyfdata.com';
    return Response.redirect(url.toString(), 301);
  }
  return next();
}
