"""Verify every registered MCP tool has a description and per-param docs.

Run:  python -m mcp_.check_docstrings [excel|schedule|whatsapp|facebook|insta]
Exit code 1 if any tool has a short description or an undocumented parameter.
"""
from __future__ import annotations

import argparse
import asyncio

from mcp.server.fastmcp import FastMCP

from mcp_.tools.excel_service import register_excel_tools
from mcp_.tools.schedule_service import register_schedule_tools
from mcp_.tools.whatsapp_service import register_whatsapp_tools
from mcp_.tools.facebook_service import register_facebook_tools
from mcp_.tools.insta_service import register_instagram_tools

REGISTRARS = {
    "excel": register_excel_tools,
    "schedule": register_schedule_tools,
    "whatsapp": register_whatsapp_tools,
    "facebook": register_facebook_tools,
    "insta": register_instagram_tools,
}

MIN_DESCRIPTION_LEN = 20


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "service",
        nargs="?",
        choices=list(REGISTRARS),
        help="check one service (default: all)",
    )
    args = parser.parse_args()

    mcp = FastMCP("docstring-check")
    for name, registrar in REGISTRARS.items():
        if args.service and name != args.service:
            continue
        registrar(mcp)

    tools = asyncio.run(mcp.list_tools())
    problems = 0
    for tool in sorted(tools, key=lambda t: t.name):
        props = (tool.inputSchema or {}).get("properties", {})
        desc_len = len((tool.description or "").strip())
        missing = [
            p
            for p, s in props.items()
            if not ((s or {}).get("description") or "").strip()
        ]
        if desc_len < MIN_DESCRIPTION_LEN or missing:
            problems += 1
            print(f"FAIL {tool.name}: desc_len={desc_len} missing={missing}")
        else:
            print(f"ok   {tool.name}")

    print(f"\n{len(tools)} tools, {problems} need work")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
