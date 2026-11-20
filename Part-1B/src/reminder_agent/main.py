"""Command-line entry point for processing one reminder request."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime

from reminder_agent.engine import process_request
from reminder_agent.models import ResolutionContext
from reminder_agent.output import clarification_response, serialize_response


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a reminder request to JSON.")
    parser.add_argument("request", help="Natural-language reminder request")
    parser.add_argument("--reference-time", help="Aware ISO 8601 reference time")
    parser.add_argument("--timezone", help="Configured IANA time zone")
    parser.add_argument(
        "--reminder-task",
        action="append",
        default=[],
        help="Existing reminder task candidate; may be supplied more than once",
    )
    args = parser.parse_args(argv)

    try:
        reference_time = (
            datetime.fromisoformat(args.reference_time.replace("Z", "+00:00"))
            if args.reference_time
            else None
        )
    except ValueError:
        response = clarification_response("What valid reference date and time should I use?")
    else:
        context = ResolutionContext(
            reference_time=reference_time,
            timezone=args.timezone,
            reminder_tasks=tuple(args.reminder_task),
        )
        response = process_request(args.request, context)

    print(serialize_response(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
