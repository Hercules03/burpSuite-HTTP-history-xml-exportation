#!/usr/bin/env python3
"""Convert a Burp Suite HTTP history XML export to CSV or HTML.

Examples:
    python3 burp_history_export.py data/eg_HTTP_History.xml
    python3 burp_history_export.py data/eg_HTTP_History.xml --format html
    python3 burp_history_export.py data/eg_HTTP_History.xml -f csv -o output/history.csv

Without --output the file is written to output/<input name>.<format>
next to this script.
"""

import argparse
import base64
import csv
import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

COLUMNS = [
    "index", "time", "method", "url", "host", "host_ip", "port", "protocol",
    "path", "extension", "status", "response_length", "mimetype", "comment",
    "request", "response",
]


def decode_body(element):
    """Return the text of a <request>/<response> element, decoding base64 when flagged."""
    if element is None or element.text is None:
        return ""
    if element.get("base64", "false").lower() == "true":
        return base64.b64decode(element.text).decode("utf-8", errors="replace")
    return element.text


def load_items(xml_path):
    root = ET.parse(xml_path).getroot()
    rows = []
    for index, item in enumerate(root.findall("item"), start=1):
        host = item.find("host")
        rows.append({
            "index": index,
            "time": item.findtext("time", ""),
            "method": item.findtext("method", ""),
            "url": item.findtext("url", ""),
            "host": host.text if host is not None and host.text else "",
            "host_ip": host.get("ip", "") if host is not None else "",
            "port": item.findtext("port", ""),
            "protocol": item.findtext("protocol", ""),
            "path": item.findtext("path", ""),
            "extension": item.findtext("extension", ""),
            "status": item.findtext("status", ""),
            "response_length": item.findtext("responselength", ""),
            "mimetype": item.findtext("mimetype", ""),
            "comment": item.findtext("comment", ""),
            "request": decode_body(item.find("request")),
            "response": decode_body(item.find("response")),
        })
    return root.get("burpVersion", ""), root.get("exportTime", ""), rows


def write_csv(rows, out_path):
    # utf-8-sig adds a BOM so Excel opens non-ASCII request/response text correctly.
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


HTML_STYLE = """
body { font-family: -apple-system, Helvetica, Arial, sans-serif; margin: 1.5rem; color: #222; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; position: sticky; top: 0; }
td.url { word-break: break-all; max-width: 420px; }
details summary { cursor: pointer; color: #0550ae; }
pre { background: #f6f8fa; padding: 8px; overflow: auto; max-height: 400px;
      white-space: pre-wrap; word-break: break-all; }
"""


def write_html(rows, out_path, burp_version, export_time):
    e = html.escape
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>Burp HTTP history</title><style>{HTML_STYLE}</style></head><body>",
        "<h1>Burp Suite HTTP history</h1>",
        f"<p>{len(rows)} items"
        + (f" &middot; Burp {e(burp_version)}" if burp_version else "")
        + (f" &middot; exported {e(export_time)}" if export_time else "")
        + "</p>",
        "<table><tr><th>#</th><th>Time</th><th>Method</th><th>URL</th>"
        "<th>Status</th><th>Length</th><th>MIME</th><th>Comment</th>"
        "<th>Request / Response</th></tr>",
    ]
    for r in rows:
        parts.append(
            "<tr>"
            f"<td>{r['index']}</td>"
            f"<td>{e(r['time'])}</td>"
            f"<td>{e(r['method'])}</td>"
            f'<td class="url">{e(r["url"])}</td>'
            f"<td>{e(r['status'])}</td>"
            f"<td>{e(r['response_length'])}</td>"
            f"<td>{e(r['mimetype'])}</td>"
            f"<td>{e(r['comment'])}</td>"
            "<td><details><summary>show</summary>"
            f"<p><b>Request</b></p><pre>{e(r['request'])}</pre>"
            f"<p><b>Response</b></p><pre>{e(r['response'])}</pre>"
            "</details></td>"
            "</tr>"
        )
    parts.append("</table></body></html>")
    out_path.write_text("\n".join(parts), encoding="utf-8")


def ask(prompt, default=None, valid=None):
    """Prompt until a non-empty (and, if given, valid) answer is entered."""
    while True:
        suffix = f" [{default}]" if default else ""
        answer = input(f"{prompt}{suffix}: ").strip() or default or ""
        if answer and (valid is None or answer.lower() in valid):
            return answer


def main():
    parser = argparse.ArgumentParser(
        description="Convert Burp Suite HTTP history XML to CSV or HTML. "
                    "Anything not given as an option is asked for interactively.")
    parser.add_argument("input", type=Path, nargs="?",
                        help="Burp Suite HTTP history XML export")
    parser.add_argument("-f", "--format", choices=["csv", "html"],
                        help="output format (asked if omitted; csv when not interactive)")
    parser.add_argument("-o", "--output", type=Path,
                        help="output file or directory (default: output/<input name>.<format>)")
    args = parser.parse_args()

    interactive = sys.stdin.isatty()

    if args.input is None:
        if not interactive:
            parser.error("the following arguments are required: input")
        while True:
            args.input = Path(ask("Input XML file path")).expanduser()
            if args.input.is_file():
                break
            print(f"file not found: {args.input}")

    if args.format is None:
        args.format = ask("Output format (csv/html)", "csv", {"csv", "html"}).lower() if interactive else "csv"

    default_out = OUTPUT_DIR / f"{args.input.stem}.{args.format}"
    if args.output is None and interactive:
        args.output = Path(ask("Output path", str(default_out))).expanduser()
    out_path = (args.output or default_out).expanduser()
    if out_path.is_dir():
        out_path = out_path / f"{args.input.stem}.{args.format}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        burp_version, export_time, rows = load_items(args.input)
    except ET.ParseError as exc:
        print(f"error: could not parse {args.input}: {exc}", file=sys.stderr)
        return 1

    if args.format == "csv":
        write_csv(rows, out_path)
    else:
        write_html(rows, out_path, burp_version, export_time)

    print(f"wrote {len(rows)} items to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
