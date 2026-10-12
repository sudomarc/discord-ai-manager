"""One-shot Discord server audit/maintenance runner for GitHub Actions."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import discord
import requests

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "server_policy.json"
POLICY = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
MODE = os.environ.get("MANAGER_MODE", "audit").lower()
CONFIRM = os.environ.get("CONFIRM_APPLY", "")
REPORT_CHANNEL_ID = os.environ.get("DISCORD_REPORT_CHANNEL_ID", "").strip()

intents = discord.Intents.none()
intents.guilds = True
client = discord.Client(intents=intents)


def inventory_guild(guild: discord.Guild) -> dict[str, Any]:
    """Return a minimal, non-sensitive inventory; no message contents are collected."""
    return {
        "guild_id": guild.id,
        "guild_name": guild.name,
        "member_count": guild.member_count,
        "channels": [
            {
                "id": channel.id,
                "name": channel.name,
                "type": str(channel.type),
                "category": channel.category.name if channel.category else None,
                "topic": getattr(channel, "topic", None),
            }
            for channel in sorted(guild.channels, key=lambda c: (c.position, c.id))
        ],
        "roles": [
            {"name": role.name, "managed": role.managed, "is_default": role.is_default()}
            for role in guild.roles
            if not role.managed
        ],
    }


def ask_openrouter(inventory: dict[str, Any]) -> str:
    if not OPENROUTER_KEY:
        return "OpenRouter non configuré : audit local effectué, analyse IA ignorée."
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es un auditeur prudent de serveurs Discord. Analyse uniquement "
                    "l'inventaire fourni. Réponds en français, en texte concis avec les "
                    "problèmes observés et des recommandations. Ne prétends pas avoir "
                    "effectué de changements. Ne recommande aucune suppression ni "
                    "modification de permissions sans revue humaine."
                ),
            },
            {"role": "user", "content": json.dumps(inventory, ensure_ascii=False)[: int(POLICY["max_ai_inventory_chars"])]},
        ],
        "max_tokens": int(POLICY["max_ai_response_tokens"]),
        "temperature": 0.2,
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/sudomarc/discord-ai-manager",
            "X-Title": "Discord AI Manager",
        },
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def safe_channel_name(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,90}", value))


async def organize_guild(guild: discord.Guild) -> list[str]:
    """Create only policy-listed text channels that are missing; never delete or edit permissions."""
    created: list[str] = []
    existing = {channel.name for channel in guild.text_channels}
    me = guild.me
    if me is None or not me.guild_permissions.manage_channels:
        raise PermissionError(f"Missing Manage Channels permission in guild {guild.id}")
    for item in POLICY["standard_text_channels"]:
        name = item["name"]
        if not safe_channel_name(name):
            raise ValueError(f"Unsafe channel name in policy: {name!r}")
        if name in existing:
            continue
        topic = str(item.get("topic", ""))[:1024] or None
        await guild.create_text_channel(
            name=name,
            topic=topic,
            reason="Discord AI Manager: explicitly approved maintenance run",
        )
        created.append(name)
    return created


async def send_report(guild: discord.Guild, text: str) -> None:
    if not REPORT_CHANNEL_ID:
        return
    try:
        channel_id = int(REPORT_CHANNEL_ID)
    except ValueError:
        print("DISCORD_REPORT_CHANNEL_ID is not a numeric channel ID; report remains in Actions logs.")
        return
    channel = guild.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        # Discord message limit is 2000 chars.
        await channel.send(text[:1900], allowed_mentions=discord.AllowedMentions.none())


@client.event
async def on_ready() -> None:
    try:
        if not client.guilds:
            raise RuntimeError("The bot is not installed in any Discord server.")
        for guild in client.guilds:
            inventory = inventory_guild(guild)
            print(f"\n## Audit: {guild.name} ({guild.id})")
            print(f"Members: {inventory['member_count']}; channels: {len(inventory['channels'])}; roles: {len(inventory['roles'])}")
            ai_report = await asyncio.to_thread(ask_openrouter, inventory)
            report = f"**Discord AI Manager — {MODE}**\nServeur : {guild.name}\n\n{ai_report}"
            if MODE == "organize":
                if CONFIRM != "APPLY":
                    raise RuntimeError("Maintenance refused: set workflow input confirm_apply to exactly APPLY.")
                created = await organize_guild(guild)
                change_report = (
                    "Aucun salon manquant selon la politique."
                    if not created
                    else "Salons créés : " + ", ".join(f"`{name}`" for name in created)
                )
                report += "\n\n**Changements appliqués**\n" + change_report
            elif MODE != "audit":
                raise ValueError("MANAGER_MODE must be 'audit' or 'organize'.")
            print(report)
            await send_report(guild, report)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    client.run(TOKEN, log_handler=None)
