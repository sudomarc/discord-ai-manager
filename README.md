# Discord AI Manager

A one-shot Discord server auditor and conservative maintenance worker, run entirely through GitHub Actions and powered by OpenRouter.

## Capabilities

- Scheduled server inventory and AI-generated recommendations.
- Manual audit runs from the GitHub Actions tab.
- Explicitly approved maintenance that creates missing standard text channels from `config/server_policy.json`.
- Optional report delivery to a Discord text channel.
- Unit tests run before each task.

It does **not** stay connected 24/7, process every message in real time, or execute arbitrary instructions returned by the model. Scheduled Actions may be delayed by GitHub.

## Quick start

1. Follow [the setup guide](docs/SETUP.md) to create a Discord bot and add the `DISCORD_BOT_TOKEN` and `OPENROUTER_API_KEY` repository secrets.
2. Optionally set `OPENROUTER_MODEL` and `DISCORD_REPORT_CHANNEL_ID` as repository variables.
3. Open **Actions → Discord AI audit → Run workflow** to test an audit.
4. To create missing standard channels, use **Actions → Discord AI manual task**, choose `organize`, and type exactly `APPLY`. The bot needs Manage Channels for this operation.

Never commit API keys or bot tokens. Do not grant Administrator; grant only the permissions needed for the chosen tasks.

## Repository layout

- `.github/workflows/discord-audit.yml` — scheduled and manual audit.
- `.github/workflows/discord-manual.yml` — manually selected audit/maintenance.
- `src/discord_ai_manager.py` — one-shot Discord runner and OpenRouter integration.
- `config/server_policy.json` — conservative channel policy.
- `tests/` — policy tests.
- `docs/SETUP.md` — setup and troubleshooting.

See [Setup](docs/SETUP.md) for full instructions.
