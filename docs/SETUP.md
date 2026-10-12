# Setup

## 1. Create a Discord bot

1. In the Discord Developer Portal, create an application and add a bot.
2. Copy its token into a GitHub Actions secret named `DISCORD_BOT_TOKEN`. Never commit the token or paste it into chat.
3. Invite the bot to the intended server with **View Channels**, **Send Messages** (if reporting to a channel), **Read Message History** is not needed, and **Manage Channels** only if you intend to run the explicitly confirmed `organize` task.
4. Do not grant Administrator. For an audit-only installation, do not grant Manage Channels.

## 2. Configure GitHub

In the repository, open **Settings → Secrets and variables → Actions**.

Add repository secrets:
- `DISCORD_BOT_TOKEN` — Discord bot token.
- `OPENROUTER_API_KEY` — OpenRouter API key.

Optional repository variables:
- `OPENROUTER_MODEL` — defaults to `openrouter/free`.
- `DISCORD_REPORT_CHANNEL_ID` — numeric ID of a text channel where the bot may post reports. Leave unset to keep reports in Actions logs.

## 3. Run it

- **Actions → Discord AI audit → Run workflow** runs an audit immediately.
- The scheduled audit runs every six hours. GitHub may delay scheduled workflows during busy periods.
- **Actions → Discord AI manual task** lets you choose `audit` or `organize`.
- `organize` requires typing exactly `APPLY`. It creates only the standard text channels listed in `config/server_policy.json` when missing. It never deletes channels or changes role permissions.

## 4. What this is and isn't

This is a one-shot GitHub Actions worker, not a permanently connected Discord bot. It runs on a schedule or when manually dispatched; it does not react to every Discord message in real time or provide always-on slash commands. Actions can be delayed or skipped by GitHub scheduling, and public repositories should be reviewed carefully before exposing workflow logs.

The OpenRouter model receives a limited server inventory (channel names/topics and role names, not message contents). If OpenRouter fails or no key is configured, the run fails or reports that AI analysis was skipped; no AI-generated instructions are executed as code.

## Troubleshooting

- **Bot sees no servers:** verify it was invited to the intended server.
- **Missing Access / Forbidden:** check channel visibility and, for `organize`, the Manage Channels permission.
- **OpenRouter 401/402/429:** check the key, model availability, account limits, and free-tier quotas.
- **No report in Discord:** verify `DISCORD_REPORT_CHANNEL_ID` and that the bot can view and send messages in that channel.
