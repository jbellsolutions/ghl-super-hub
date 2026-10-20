# Share and maintain the toolkit

- Repository: https://github.com/jbellsolutions/ghl-super-hub
- Permanent one-pager: https://jbellsolutions.github.io/ghl-super-hub/
- here.now one-pager: https://open-spirit-656x.here.now/
- Installable bundle: https://github.com/jbellsolutions/ghl-super-hub/releases/latest

The here.now publication was created anonymously. Its API-reported expiry is
2026-10-21 at 09:33 UTC unless the owner claims it. The private claim link is supplied
to the owner in chat and is deliberately excluded from source control. GitHub Pages
is the lasting fallback and serves the same source from `site/`.

The public repository is exported from an explicit package allowlist, not the private
workspace history. Credentials, original attachments, account-specific builders and
sample account exports are excluded. The search database is generated locally from
tracked article/specification sources; downloadable releases can include the index.

## Share the one-command setup

Send the repository URL plus [INSTALL-AGENT.md](../INSTALL-AGENT.md), or this command:

```bash
curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash
```

It detects installed agents; append `-s -- --agent claude` or `-s -- --agent hermes`
to `bash` to select one. A GHL token and browser authentication remain one-time setup.
The script verifies the published release checksum before installation.

## Work on this public repository

Normal cloned repositories use ordinary commits and pull requests. Before pushing:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_bundle.py
git diff --check
git pull --rebase
git push
```

GitHub Actions verifies the toolkit on pushes/PRs. A separate workflow publishes
`site/` to GitHub Pages when its source changes. No here.now API key is needed for
GitHub Pages. To make a fresh here.now publication from another checkout:

```bash
.venv/bin/python scripts/publish_here_now.py
# Subsequent updates from the same checkout:
.venv/bin/python scripts/publish_here_now.py --update
```

A key in `HERENOW_API_KEY` or `~/.herenow/credentials` uses authenticated publishing.
Otherwise the provider creates an expiring anonymous Site. The script stores the
claim and update credentials under ignored `.publish/`, with private file permissions.
Do not copy that state directory into a release or commit it. An API key alone does
not claim an existing anonymous Site; use the provider's claim flow.

## Export from the original private workspace

```bash
.venv/bin/python scripts/build_bundle.py
.venv/bin/python scripts/export_repository.py /new/empty/destination
```

Review the exported files before publishing. Never push the original workspace's
Git history to the public repository; it contains upstream account-specific examples.
