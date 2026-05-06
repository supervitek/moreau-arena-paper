# Plain Site Care Hosting

Plain Site Care is hosted from the same Render web service as Moreau Arena.

## Routing Model

The FastAPI app serves different public sites based on the request host:

- `moreauarena.com` and `www.moreauarena.com` keep serving the Moreau Arena site.
- `plainsitecare.com` and `www.plainsitecare.com` serve the Plain Site Care landing page.

The Plain Site Care static files live in:

```text
web/static/plain-site-care/
```

The host switch is implemented in `web/app.py` through `PLAIN_SITE_CARE_HOSTS`.
The default value is:

```text
plainsitecare.com,www.plainsitecare.com
```

Override it on Render only if the domain list changes.

## Render Setup Needed

In the existing Moreau Arena Render web service:

1. Add `plainsitecare.com` as a custom domain.
2. Add `www.plainsitecare.com` as a custom domain.
3. Use the DNS targets Render gives for those domains.

No second Render service is required for the current traffic level.

## Cloudflare DNS Needed

In Cloudflare for `plainsitecare.com`:

1. Point the apex domain to the Render custom-domain target.
2. Point `www` to the Render custom-domain target.
3. Keep future email records separate from web hosting records:
   - MX
   - SPF
   - DKIM
   - DMARC

Cloudflare can flatten CNAME records at the apex, but the exact record type should follow Render's custom-domain instructions in the dashboard.

## Local Verification

Run the app locally:

```bash
.venv/bin/python -m uvicorn web.app:app --host 127.0.0.1 --port 8015
```

Verify host routing:

```bash
curl -H 'Host: plainsitecare.com' http://127.0.0.1:8015/
curl -H 'Host: moreauarena.com' http://127.0.0.1:8015/
curl -o /dev/null -w '%{http_code}' -H 'Host: plainsitecare.com' http://127.0.0.1:8015/nope
```

Expected result:

- Plain Site Care content on `plainsitecare.com`
- Moreau Arena content on `moreauarena.com`
- `404` for missing Plain Site Care paths
