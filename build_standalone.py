"""
Build a self-contained HTML file (no server needed) by inlining content.json
into app_template.html. Open the result directly in any browser.

    python build_standalone.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "Databricks DE Associate - Study Hub.html"


def main():
    content = json.loads((HERE / "content.json").read_text(encoding="utf-8"))
    html = (HERE / "app_template.html").read_text(encoding="utf-8")
    payload = json.dumps(content).replace("</", "<\\/")  # safe inside <script>
    html = html.replace("__CONTENT_JSON__", payload)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.name} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
