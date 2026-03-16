# Browser Playtests

Checked-in browser regression pack for island flows. This suite is meant to catch real UI/runtime regressions that raw HTTP smoke checks miss.

Install once:

```bash
cd scripts/playtests
npm install
```

Run against a local app:

```bash
cd scripts/playtests
npm run island-regression -- --base-url http://127.0.0.1:8000
```

The suite uses the locally installed Chrome by default. Override with:

```bash
MOREAU_PLAYWRIGHT_EXECUTABLE=\"/path/to/Chrome\" npm run island-regression -- --base-url http://127.0.0.1:8000
```
