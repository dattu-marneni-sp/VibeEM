#!/usr/bin/env python3
"""
Post a weekly Data Engineering production-support summary to Slack.

Default destination: DM / conversation D072F01EZEH
  https://sailpoint.slack.com/archives/D072F01EZEH

Schedule (Monday 08:00 America/New_York):
  - macOS: use launchd (example plist in docstring at bottom of this file).
  - Generic cron (if your crond honors CRON_TZ):
      CRON_TZ=America/New_York 0 8 * * 1 /path/to/python /path/to/weekly_de_support_report.py

Environment variables
---------------------
Required:
  SLACK_BOT_TOKEN   Slack bot token (xoxb-...) with chat:write.
                    For a DM (D...), the bot must have been invited / the DM
                    must exist with the bot (open a DM to the app first).

Optional:
  SLACK_CHANNEL     Override channel or DM id (default: D072F01EZEH).
  ROOTLY_API_KEY    If set, pulls alert/incident counts from Rootly REST API.
  ROOTLY_TEAM_ID   Rootly team / group id for filter[groups] (default: Data
                    Engineering team id used in this repo’s Team/Observability).

Flags:
  --dry-run         Build the report and print to stdout; do not post to Slack.
  --now ISO         For tests only; use a *Monday* morning time in America/New_York
                    to match the same week window the cron job will use.

macOS: see scripts/com.vibeem.weekly-de-report.plist.example (Monday 08:00, TZ set).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Default Slack destination (DM / conversation id from archives URL).
DEFAULT_SLACK_CHANNEL = "D072F01EZEH"

# Data Engineering Rootly team id (from Team/Observability).
DEFAULT_ROOTLY_TEAM_ID = "dbb67ed7-7125-43c4-851e-6b7a2d443f49"

ROOTLY_BASE = "https://api.rootly.com/v1"
SLACK_API = "https://slack.com/api/chat.postMessage"


@dataclass(frozen=True)
class WeekWindow:
    label: str
    start_utc: datetime
    end_utc: datetime


def previous_calendar_week_et(*, now: datetime | None = None) -> WeekWindow:
    """
    Calendar week Monday 00:00 .. Sunday 23:59:59.999999 in America/New_York,
    for the week *before* the current ISO week (the week that just ended if
    today is Monday).
    """
    tz = ZoneInfo("America/New_York")
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)

    today = now.date()
    this_monday = today - timedelta(days=today.weekday())
    this_monday_midnight = datetime.combine(this_monday, datetime.min.time(), tzinfo=tz)
    prev_monday = this_monday_midnight - timedelta(days=7)
    week_end = this_monday_midnight - timedelta(microseconds=1)
    start_utc = prev_monday.astimezone(ZoneInfo("UTC"))
    end_utc = week_end.astimezone(ZoneInfo("UTC"))
    label = f"{prev_monday.date()} – {week_end.date()} (America/New_York)"
    return WeekWindow(label=label, start_utc=start_utc, end_utc=end_utc)


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def rootly_count_alerts(
    api_key: str,
    team_id: str,
    week: WeekWindow,
) -> tuple[int | None, str | None]:
    """Return (total_count, error_message)."""
    params = {
        "page[number]": "1",
        "page[size]": "1",
        "fields[alerts]": "id",
        "filter[groups]": team_id,
        "filter[started_at][gte]": _iso_z(week.start_utc),
        "filter[started_at][lte]": _iso_z(week.end_utc),
    }
    q = urllib.parse.urlencode(params)
    url = f"{ROOTLY_BASE}/alerts?{q}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = str(e)
        return None, f"Rootly alerts HTTP {e.code}: {detail}"
    except Exception as e:
        return None, f"Rootly alerts error: {e}"

    meta = body.get("meta") or {}
    total = meta.get("total_count")
    if isinstance(total, int):
        return total, None
    return None, "Rootly alerts: missing meta.total_count"


def rootly_count_incidents(
    api_key: str,
    team_id: str,
    week: WeekWindow,
) -> tuple[int | None, str | None]:
    """Return (total_count, error_message). Rootly schema may vary by org."""
    params = {
        "page[number]": "1",
        "page[size]": "1",
        "filter[team_ids]": team_id,
        "filter[started_at][gte]": _iso_z(week.start_utc),
        "filter[started_at][lte]": _iso_z(week.end_utc),
    }
    q = urllib.parse.urlencode(params)
    url = f"{ROOTLY_BASE}/incidents?{q}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = str(e)
        return None, f"Rootly incidents HTTP {e.code}: {detail}"
    except Exception as e:
        return None, f"Rootly incidents error: {e}"

    meta = body.get("meta") or {}
    total = meta.get("total_count")
    if isinstance(total, int):
        return total, None
    return None, "Rootly incidents: missing meta.total_count (non-fatal)"


def build_report(
    week: WeekWindow,
    *,
    alerts: int | None,
    incidents: int | None,
    rootly_notes: list[str],
) -> str:
    lines = [
        f"*Data Engineering — weekly production support*",
        f"_Reporting week (ET):_ `{week.label}`",
        f"_UTC window used for APIs:_ `{_iso_z(week.start_utc)}` → `{_iso_z(week.end_utc)}`",
        "",
    ]
    if alerts is not None:
        lines.append(f"• *Rootly alerts* (team group): *{alerts}*")
    else:
        lines.append("• *Rootly alerts:* not fetched (set `ROOTLY_API_KEY`)")

    if incidents is not None:
        lines.append(f"• *Rootly incidents* (team id filter): *{incidents}*")
    elif any("incidents" in n.lower() for n in rootly_notes):
        lines.append("• *Rootly incidents:* see notes below")
    else:
        lines.append("• *Rootly incidents:* not fetched (set `ROOTLY_API_KEY`)")

    lines.extend(
        [
            "",
            "*Prod coordination channel:* `#team-data-enginering-prod-only-alerts`",
            "*Non-prod alerts:* `#team-data-engineering-nonprod-alerts`",
            "*On-call schedule:* `#team-data-engineering-oncall-schedule`",
            "",
            "_Template — add bullets manually or extend this script (Jira, Grafana links, P1 threads)._",
            "• Major incidents / customer impact:",
            "• Themes (Flink / DIP, Airflow, Snowflake, search rollout, etc.):",
            "• Mitigations & follow-ups:",
        ]
    )
    if rootly_notes:
        lines.append("")
        lines.append("*API notes*")
        for n in rootly_notes:
            lines.append(f"• {n}")
    return "\n".join(lines)


def slack_post_message(token: str, channel: str, text: str) -> None:
    payload = {
        "channel": channel,
        "text": text,
        "mrkdwn": True,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SLACK_API,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Slack HTTP {e.code}: {detail}") from e

    if not body.get("ok"):
        raise SystemExit(f"Slack API error: {body}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report to stdout and skip Slack.",
    )
    parser.add_argument(
        "--now",
        metavar="ISO",
        help="Override current time for week calculation (ISO8601 with offset), for tests.",
    )
    args = parser.parse_args()

    if args.now:
        raw = args.now
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        now = datetime.fromisoformat(raw)
    else:
        now = None

    week = previous_calendar_week_et(now=now)

    api_key = os.environ.get("ROOTLY_API_KEY", "").strip()
    team_id = os.environ.get("ROOTLY_TEAM_ID", DEFAULT_ROOTLY_TEAM_ID).strip()

    alerts: int | None = None
    incidents: int | None = None
    notes: list[str] = []

    if api_key:
        ac, err = rootly_count_alerts(api_key, team_id, week)
        if err:
            notes.append(err)
        else:
            alerts = ac

        ic, ierr = rootly_count_incidents(api_key, team_id, week)
        if ierr:
            notes.append(ierr)
        else:
            incidents = ic
    else:
        notes.append("`ROOTLY_API_KEY` not set — skipping Rootly metrics.")

    text = build_report(week, alerts=alerts, incidents=incidents, rootly_notes=notes)

    if args.dry_run:
        print(text)
        return 0

    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        print("SLACK_BOT_TOKEN is required unless --dry-run.", file=sys.stderr)
        return 1

    channel = os.environ.get("SLACK_CHANNEL", DEFAULT_SLACK_CHANNEL).strip()
    slack_post_message(token, channel, text)
    print(f"Posted weekly report to Slack channel/DM {channel}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
