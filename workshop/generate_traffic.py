#!/usr/bin/env python3
"""Generate demo traffic for the PO/PM Langfuse workshop — black-box, over HTTP.

Drives the *running* RAG app through its public HTTP API (``/chat`` and
``/feedback``), exactly as a browser would. It imports nothing from the app and
changes nothing in ``src/`` — point it at a running instance and it populates
whatever Langfuse project that instance is configured for.

Because it goes through the real endpoints, every trace, span, session and score
it produces is identical to genuine user traffic — including the retrieval span,
token cost, latency/TTFT, and the ``sherlock-holmes`` tag that ``task
dataset:seed`` filters on.

Typical use (app running at http://localhost:7932, pointed at your empty project):

    python3 workshop/generate_traffic.py                 # main populate pass
    python3 workshop/generate_traffic.py --list          # show scenarios, send nothing
    python3 workshop/generate_traffic.py --only healthy,hard
    python3 workshop/generate_traffic.py --only starved --session-prefix "starved-"

No dependencies beyond the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:7932"
DEFAULT_QUESTIONS = Path(__file__).with_name("questions.json")
FEEDBACK_VALUE = {"up": 1, "down": -1}


def _post(url: str, payload: dict, timeout: float):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    return urllib.request.urlopen(req, timeout=timeout)


def post_chat(base_url: str, question: str, session_id: str, timeout: float = 180.0):
    """Send one turn, parse the SSE stream, return (trace_id, answer_text)."""
    trace_id: str | None = None
    parts: list[str] = []
    with _post(f"{base_url}/chat", {"question": question, "session_id": session_id}, timeout) as resp:
        for raw in resp:  # server streams line-by-line; iterate as it arrives
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            body = line[len("data:"):].strip()
            if body == "[DONE]":
                break
            try:
                obj = json.loads(body)
            except json.JSONDecodeError:
                continue
            if "trace_id" in obj:
                trace_id = obj["trace_id"]
            elif "delta" in obj:
                parts.append(obj["delta"])
    return trace_id, "".join(parts)


def post_feedback(base_url: str, trace_id: str, value: int, timeout: float = 30.0) -> None:
    with _post(f"{base_url}/feedback", {"trace_id": trace_id, "value": value}, timeout) as resp:
        resp.read()


def health_ok(base_url: str, timeout: float = 5.0) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def load_conversations(path: Path, only: set[str] | None) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    convs = data.get("conversations", [])
    if only:
        return [c for c in convs if c.get("group") in only]
    # default: everything except conversations explicitly opted out (e.g. "starved")
    return [c for c in convs if c.get("default_run", True)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"App base URL (default {DEFAULT_BASE_URL})")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS, help="Path to questions.json")
    parser.add_argument("--only", default="", help="Comma-separated groups to run (e.g. healthy,hard,out_of_corpus,multilingual,starved)")
    parser.add_argument("--session-prefix", default="", help="Prefix prepended to every session id (use per env pass, e.g. 'starved-')")
    parser.add_argument("--no-feedback", action="store_true", help="Do not send 👍/👎 feedback")
    parser.add_argument("--delay", type=float, default=0.6, help="Seconds to pause between turns (default 0.6)")
    parser.add_argument("--limit", type=int, default=0, help="Max conversations to run (0 = no limit)")
    parser.add_argument("--list", action="store_true", help="List selected scenarios and exit — sends nothing")
    args = parser.parse_args()

    only = {g.strip() for g in args.only.split(",") if g.strip()} or None
    convs = load_conversations(args.questions, only)
    if args.limit:
        convs = convs[: args.limit]

    if not convs:
        print("No conversations selected. Check --only against the groups in questions.json.")
        return 1

    if args.list:
        print(f"{len(convs)} conversation(s) selected:\n")
        for c in convs:
            sid = f"{args.session_prefix}{c['session']}"
            print(f"  [{c.get('group', '?'):13}] session={sid}  ({len(c['turns'])} turn(s))")
            for t in c["turns"]:
                fb = t.get("feedback", "none")
                mark = {"up": "👍", "down": "👎", "none": "  "}.get(fb, "  ")
                print(f"       {mark} {t['q']}")
        return 0

    if not health_ok(args.base_url):
        print(f"App not reachable at {args.base_url} (GET /health failed).")
        print("Start it first (e.g. `task run`) and confirm it's pointed at your Langfuse project.")
        return 2

    total_turns = sum(len(c["turns"]) for c in convs)
    print(f"Sending {total_turns} turn(s) across {len(convs)} session(s) to {args.base_url}\n")

    sent = fb_sent = errors = 0
    for c in convs:
        session_id = f"{args.session_prefix}{c['session']}"
        group = c.get("group", "?")
        print(f"● session '{session_id}'  [{group}]")
        for t in c["turns"]:
            q = t["q"]
            try:
                trace_id, answer = post_chat(args.base_url, q, session_id)
            except urllib.error.URLError as e:
                errors += 1
                print(f"    ✗ chat failed: {e}  — {q[:60]}")
                continue
            sent += 1
            snippet = " ".join(answer.split())[:70]
            print(f"    → {q[:60]}")
            print(f"      {snippet}{'…' if len(answer) > 70 else ''}")

            fb = t.get("feedback", "none")
            if not args.no_feedback and fb in FEEDBACK_VALUE and trace_id:
                try:
                    post_feedback(args.base_url, trace_id, FEEDBACK_VALUE[fb])
                    fb_sent += 1
                    print(f"      {'👍' if fb == 'up' else '👎'} feedback recorded")
                except urllib.error.URLError as e:
                    print(f"      ! feedback failed: {e}")
            if args.delay:
                time.sleep(args.delay)
        print()

    print(f"Done. {sent} turn(s) sent, {fb_sent} feedback score(s), {errors} error(s).")
    print("Traces are flowing to Langfuse (async flush — allow a few seconds).")
    print("Next: `task dataset:seed` to build the eval dataset from these traces.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
