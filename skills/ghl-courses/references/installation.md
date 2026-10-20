# Package location

For one-command installs, use `ghl` or `~/.local/bin/ghl`. The installer prints the
absolute CLI path too. For native plugin installs, the plugin root is two directories
above the skill directory. Run `bash <plugin-root>/scripts/run-hub.sh ...` there;
the first call prepares its persistent Python runtime automatically.

For a normal source checkout, use `./ghl` at the repository root. Use `ghl hub connect`
to save credentials through a hidden terminal prompt. Existing `GHL_API_KEY`,
`GHL_LOCATION_ID` and explicit `--env-file` profiles are supported. Installing a
plugin does not authorize launching campaigns or changing live GHL data.
