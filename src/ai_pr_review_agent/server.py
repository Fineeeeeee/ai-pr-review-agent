from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .deepseek_client import DEFAULT_DEEPSEEK_MODEL, attach_ai_review, request_deepseek_review
from .renderers import render_markdown
from .reviewer import review_diff


def build_home_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI PR Review Agent</title>
  <style>
    :root { color-scheme: light; --ink:#17202a; --muted:#5d6d7e; --line:#d6dbdf; --accent:#2471a3; --paper:#f7f9f9; --soft:#eef6fb; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Segoe UI, Arial, sans-serif; color: var(--ink); background: #fff; }
    header { padding: 22px 32px 12px; border-bottom: 1px solid var(--line); }
    h1 { margin: 0 0 6px; font-size: 24px; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); }
    main { display: grid; grid-template-columns: minmax(320px, .9fr) minmax(360px, 1.1fr); gap: 20px; padding: 20px 32px 32px; }
    textarea { width: 100%; min-height: 500px; resize: vertical; padding: 14px; border: 1px solid var(--line); border-radius: 6px; font: 13px Consolas, monospace; }
    button, select { height: 40px; padding: 0 14px; border: 1px solid var(--line); border-radius: 6px; background: white; color: var(--ink); font-weight: 600; }
    button.primary { border: 0; background: var(--accent); color: white; cursor: pointer; }
    button:disabled { opacity: .6; cursor: wait; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 12px 0; }
    .status { color: var(--muted); font-size: 13px; }
    .summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 12px 0; }
    .metric { padding: 10px; background: var(--soft); border: 1px solid #d8edf7; border-radius: 6px; }
    .metric span { display: block; color: var(--muted); font-size: 12px; }
    .metric strong { font-size: 18px; }
    #riskBadge { display: inline-flex; align-items: center; min-width: 92px; justify-content: center; height: 28px; padding: 0 10px; border-radius: 999px; background: #d5f5e3; color: #145a32; font-weight: 700; }
    #riskBadge.high, #riskBadge.critical { background: #fadbd8; color: #922b21; }
    #riskBadge.medium { background: #fcf3cf; color: #7d6608; }
    pre { min-height: 430px; margin: 0; padding: 14px; overflow: auto; background: var(--paper); border: 1px solid var(--line); border-radius: 6px; white-space: pre-wrap; font: 13px Consolas, monospace; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; padding: 16px; } header { padding: 20px 16px 10px; } .summary { grid-template-columns: repeat(2, 1fr); } textarea, pre { min-height: 340px; } }
  </style>
</head>
<body>
  <header>
    <h1>AI PR Review Agent</h1>
    <p>Paste a unified git diff to generate bilingual review, structured JSON, context compression, and risk summary.</p>
  </header>
  <main>
    <section>
      <div class="toolbar">
        <button class="primary" id="review">Review Diff</button>
        <button id="sample">Load Sample</button>
        <label><input id="deepseek" type="checkbox"> DeepSeek</label>
        <span class="status" id="status">Ready</span>
      </div>
      <textarea id="diff" spellcheck="false" placeholder="Paste git diff here..."></textarea>
    </section>
    <section>
      <div class="toolbar">
        <span id="riskBadge">LOW</span>
        <select id="viewMode">
          <option value="markdown">Markdown</option>
          <option value="json">Structured JSON</option>
        </select>
      </div>
      <div class="summary">
        <div class="metric"><span>Findings</span><strong id="findingCount">0</strong></div>
        <div class="metric"><span>Changed Files</span><strong id="fileCount">0</strong></div>
        <div class="metric"><span>Context</span><strong id="contextMode">-</strong></div>
        <div class="metric"><span>Auto Approve</span><strong id="autoApprove">-</strong></div>
      </div>
      <pre id="report">Report will appear here.</pre>
      <pre id="jsonView" hidden>{}</pre>
    </section>
  </main>
  <script>
    const diff = document.getElementById('diff');
    const report = document.getElementById('report');
    const jsonView = document.getElementById('jsonView');
    const status = document.getElementById('status');
    const review = document.getElementById('review');
    const deepseek = document.getElementById('deepseek');
    const viewMode = document.getElementById('viewMode');
    const riskBadge = document.getElementById('riskBadge');
    let lastData = null;
    document.getElementById('sample').onclick = () => {
      diff.value = 'diff --git a/app.py b/app.py\\n--- a/app.py\\n+++ b/app.py\\n@@ -1 +1,5 @@\\n+api_key = "demo-api-key-value"\\n+cursor.execute(f"select * from users where id = {user_id}")\\n+eval(user_input)\\n+subprocess.run(command, shell=True)\\n';
    };
    viewMode.onchange = () => renderActiveView();
    review.onclick = async () => {
      review.disabled = true;
      status.textContent = 'Reviewing...';
      try {
        const res = await fetch('/api/review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ diff: diff.value, deepseek: deepseek.checked }) });
        const data = await res.json();
        lastData = data;
        updateSummary(data);
        renderActiveView();
        status.textContent = res.ok ? 'Done' : 'Error';
      } catch (error) {
        report.textContent = String(error);
        status.textContent = 'Error';
      } finally {
        review.disabled = false;
      }
    };
    function updateSummary(data) {
      const risk = (data.risk_level || 'low').toUpperCase();
      riskBadge.textContent = risk;
      riskBadge.className = (data.risk_level || 'low');
      document.getElementById('findingCount').textContent = data.findings ? data.findings.length : 0;
      document.getElementById('fileCount').textContent = data.summary ? data.summary.changed_files.length : 0;
      document.getElementById('contextMode').textContent = data.context_plan && data.context_plan.file_strategies[0] ? data.context_plan.file_strategies[0].strategy : '-';
      document.getElementById('autoApprove').textContent = data.structured_output ? String(data.structured_output.auto_approve_eligible) : '-';
    }
    function renderActiveView() {
      if (!lastData) return;
      const showJson = viewMode.value === 'json';
      report.hidden = showJson;
      jsonView.hidden = !showJson;
      report.textContent = lastData.markdown || JSON.stringify(lastData, null, 2);
      jsonView.textContent = JSON.stringify(lastData.structured_output || lastData, null, 2);
    }
  </script>
</body>
</html>"""


def review_payload(body: bytes) -> tuple[int, dict[str, Any]]:
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return 400, {"error": "Request body must be valid JSON."}

    diff_text = payload.get("diff")
    if not isinstance(diff_text, str):
        return 400, {"error": "`diff` must be a string."}

    report = review_diff(diff_text)
    if payload.get("deepseek") is True:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return 400, {"error": "DEEPSEEK_API_KEY is required when DeepSeek enhancement is enabled."}
        model = payload.get("model") if isinstance(payload.get("model"), str) else DEFAULT_DEEPSEEK_MODEL
        try:
            ai_review = request_deepseek_review(report, diff_text, api_key=api_key, model=model)
        except RuntimeError as error:
            return 502, {"error": str(error)}
        report = attach_ai_review(report, ai_review)

    data = report.to_dict()
    data["markdown"] = render_markdown(report)
    return 200, data


class ReviewHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_json(404, {"error": "Not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(build_home_page().encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/api/review":
            self.send_json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        status, payload = review_payload(self.rfile.read(length))
        self.send_json(status, payload)

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), ReviewHandler)
    print(f"AI PR Review Agent running at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
