"""Collate Cloudflare CSV exports into a persistent, de-duplicated dataset.

This utility accepts a zip archive (or a directory) of Cloudflare CSV exports,
normalizes known export schemas, and appends only net-new rows to a persistent
history file. It then materializes CSV/JSON outputs and an interactive HTML
dashboard for quick review.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path


SchemaName = str


SCHEMA_TIME_SERIES_LABEL = "time_series_label"
SCHEMA_TIMESTAMP_VALUE = "timestamp_value"
SCHEMA_LOCATION_VALUE = "location_value"
SCHEMA_COUNTRY_REQUESTS = "country_requests"


def _now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _normalize_header(header: list[str]) -> tuple[str, ...]:
    return tuple(col.strip() for col in header)


def detect_schema(header: list[str]) -> SchemaName | None:
    h = _normalize_header(header)
    if h == ("count", "timestamp", "label", "dashed"):
        return SCHEMA_TIME_SERIES_LABEL
    if h == ("timestamp", "value"):
        return SCHEMA_TIMESTAMP_VALUE
    if h == ("value", "id.name", "id.code", "id.lat", "id.lon", "lat", "lng", "location"):
        return SCHEMA_LOCATION_VALUE
    if h == ("name", "requests"):
        return SCHEMA_COUNTRY_REQUESTS
    return None


def _to_number(text: str) -> int | float | None:
    value = text.strip()
    if not value:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return None


def _metric_from_source_name(source_name: str, default_metric: str) -> str:
    name = source_name.lower()
    metric_map = {
        "unique_visitors": "unique_visitors",
        "total_requests": "total_requests",
        "percent_cached": "percent_cached",
        "total_data_served": "total_data_served",
        "data_served": "data_served",
        "cached_requests": "cached_requests",
        "dns": "dns_value",
    }
    for marker, metric in metric_map.items():
        if marker in name:
            return metric
    return default_metric


def _extract_anchor_date(source_name: str) -> dt.date:
    # Handles names like unique_visitors_2026-06-16T21_40_55.001Z.csv
    match = re.search(r"(\d{4}-\d{2}-\d{2})", source_name)
    if match:
        return dt.date.fromisoformat(match.group(1))
    return dt.datetime.now(dt.timezone.utc).date()


def _parse_day_month_token(token: str, anchor_date: dt.date) -> dt.date | None:
    # Cloudflare exports often use values like "17 MAY" without year.
    token_norm = " ".join(token.strip().upper().split())
    match = re.fullmatch(r"(\d{1,2})\s+([A-Z]{3})", token_norm)
    if not match:
        return None

    day = int(match.group(1))
    mon = match.group(2).title()
    for candidate_year in (anchor_date.year, anchor_date.year - 1):
        try:
            candidate = dt.datetime.strptime(f"{day} {mon} {candidate_year}", "%d %b %Y").date()
        except ValueError:
            continue

        if candidate <= anchor_date and (anchor_date - candidate).days <= 370:
            return candidate

    return None


def _normalize_row(
    schema: SchemaName,
    row: dict[str, str],
    *,
    source_name: str,
    anchor_date: dt.date,
) -> dict[str, str | int | float | None]:
    if schema == SCHEMA_TIME_SERIES_LABEL:
        timestamp = row.get("timestamp", "").strip()
        date_utc = ""
        if re.match(r"^\d{4}-\d{2}-\d{2}T", timestamp):
            date_utc = timestamp[:10]

        return {
            "schema": schema,
            "metric": "dns_count_by_label",
            "timestamp_utc": timestamp,
            "date_utc": date_utc,
            "clock_time": "",
            "label": row.get("label", "").strip(),
            "country": "",
            "location": "",
            "id_code": "",
            "value": _to_number(row.get("count", "")),
            "dashed": row.get("dashed", "").strip(),
        }

    if schema == SCHEMA_TIMESTAMP_VALUE:
        raw_timestamp = row.get("timestamp", "").strip()
        parsed_date = _parse_day_month_token(raw_timestamp, anchor_date)
        base_metric = _metric_from_source_name(source_name, "time_bucket_value")

        if parsed_date is not None:
            metric = base_metric if base_metric != "time_bucket_value" else "daily_value"
            return {
                "schema": schema,
                "metric": metric,
                "timestamp_utc": parsed_date.isoformat() + "T00:00:00Z",
                "date_utc": parsed_date.isoformat(),
                "clock_time": "",
                "label": "",
                "country": "",
                "location": "",
                "id_code": "",
                "value": _to_number(row.get("value", "")),
                "dashed": "",
            }

        return {
            "schema": schema,
            "metric": base_metric,
            "timestamp_utc": "",
            "date_utc": "",
            "clock_time": raw_timestamp,
            "label": "",
            "country": "",
            "location": "",
            "id_code": "",
            "value": _to_number(row.get("value", "")),
            "dashed": "",
        }

    if schema == SCHEMA_LOCATION_VALUE:
        return {
            "schema": schema,
            "metric": "location_value",
            "timestamp_utc": "",
            "date_utc": "",
            "clock_time": "",
            "label": "",
            "country": "",
            "location": row.get("location", "").strip() or row.get("id.name", "").strip(),
            "id_code": row.get("id.code", "").strip(),
            "value": _to_number(row.get("value", "")),
            "dashed": "",
        }

    if schema == SCHEMA_COUNTRY_REQUESTS:
        return {
            "schema": schema,
            "metric": "country_requests",
            "timestamp_utc": "",
            "date_utc": "",
            "clock_time": "",
            "label": "",
            "country": row.get("name", "").strip(),
            "location": "",
            "id_code": "",
            "value": _to_number(row.get("requests", "")),
            "dashed": "",
        }

    raise ValueError(f"Unsupported schema: {schema}")


def _fingerprint(normalized: dict[str, str | int | float | None]) -> str:
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return f"{normalized['schema']}::{payload}"


def _collect_csv_paths(input_path: Path) -> tuple[list[Path], tempfile.TemporaryDirectory[str] | None]:
    if input_path.is_file() and input_path.suffix.lower() == ".csv":
        return [input_path], None

    if input_path.is_dir():
        return sorted(input_path.glob("*.csv")), None

    if input_path.suffix.lower() == ".zip":
        temp_dir = tempfile.TemporaryDirectory(prefix="cloudflare_csv_")
        with zipfile.ZipFile(input_path, "r") as archive:
            archive.extractall(temp_dir.name)
        return sorted(Path(temp_dir.name).glob("*.csv")), temp_dir

    raise ValueError("Input must be a directory containing CSV files or a .zip archive")


def _read_existing_fingerprints(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _write_fingerprints(path: Path, fingerprints: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(fingerprints)) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: list[dict[str, str | int | float | None]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, str | int | float | None]]:
    if not path.exists():
        return []
    rows: list[dict[str, str | int | float | None]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _materialize_csv(path: Path, rows: list[dict[str, str | int | float | None]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ingested_at_utc",
        "source_batch",
        "source_file",
        "schema",
        "metric",
        "timestamp_utc",
        "date_utc",
        "clock_time",
        "label",
        "country",
        "location",
        "id_code",
        "dashed",
        "value",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _aggregate_for_dashboard(rows: list[dict[str, str | int | float | None]]) -> dict[str, list[dict[str, str | int | float]]]:
    dns_by_label: dict[tuple[str, str], float] = defaultdict(float)
    dns_daily_total: dict[str, float] = defaultdict(float)
    daily_metrics: dict[tuple[str, str], float] = defaultdict(float)
    intraday_avg_acc: dict[tuple[str, str], tuple[float, int]] = defaultdict(lambda: (0.0, 0))
    country_totals: dict[str, float] = defaultdict(float)
    location_totals: dict[str, float] = defaultdict(float)

    for row in rows:
        metric = str(row.get("metric", ""))
        value = row.get("value")
        if value is None:
            continue
        numeric = float(value)

        if metric == "dns_count_by_label":
            timestamp = str(row.get("timestamp_utc", ""))
            label = str(row.get("label", "")) or "(unlabeled)"
            if timestamp:
                dns_by_label[(label, timestamp)] += numeric
                date_utc = str(row.get("date_utc", "")) or timestamp[:10]
                if date_utc:
                    dns_daily_total[date_utc] += numeric

        elif metric == "country_requests":
            country = str(row.get("country", "")) or "(unknown)"
            country_totals[country] += numeric

        elif metric == "location_value":
            location = str(row.get("location", "")) or "(unknown)"
            location_totals[location] += numeric

        else:
            date_utc = str(row.get("date_utc", ""))
            if not date_utc:
                timestamp = str(row.get("timestamp_utc", ""))
                if re.match(r"^\d{4}-\d{2}-\d{2}T", timestamp):
                    date_utc = timestamp[:10]

            clock = str(row.get("clock_time", ""))
            if date_utc:
                daily_metrics[(metric, date_utc)] += numeric
            elif clock:
                total, count = intraday_avg_acc[(metric, clock)]
                intraday_avg_acc[(metric, clock)] = (total + numeric, count + 1)

    dns_label_series = [
        {"label": label, "timestamp": timestamp, "value": value}
        for (label, timestamp), value in sorted(dns_by_label.items(), key=lambda x: (x[0][0], x[0][1]))
    ]

    dns_daily_series = [
        {"date": date_utc, "value": total}
        for date_utc, total in sorted(dns_daily_total.items(), key=lambda x: x[0])
    ]

    daily_metric_series = [
        {"metric": metric, "date": date_utc, "value": total}
        for (metric, date_utc), total in sorted(daily_metrics.items(), key=lambda x: (x[0][0], x[0][1]))
    ]

    metric_totals_acc: dict[str, float] = defaultdict(float)
    metric_latest_date: dict[str, str] = {}
    metric_latest_value: dict[str, float] = {}
    for item in daily_metric_series:
        metric = str(item["metric"])
        date_utc = str(item["date"])
        value = float(item["value"])
        metric_totals_acc[metric] += value
        if metric not in metric_latest_date or date_utc > metric_latest_date[metric]:
            metric_latest_date[metric] = date_utc
            metric_latest_value[metric] = value

    metric_totals = [
        {
            "metric": metric,
            "total": total,
            "latest_date": metric_latest_date.get(metric, ""),
            "latest_value": metric_latest_value.get(metric, 0.0),
        }
        for metric, total in sorted(metric_totals_acc.items(), key=lambda x: x[1], reverse=True)
    ]

    intraday_series = [
        {
            "metric": metric,
            "clock_time": clock_time,
            "avg_value": total / count if count else 0.0,
            "samples": count,
        }
        for (metric, clock_time), (total, count) in sorted(intraday_avg_acc.items(), key=lambda x: (x[0][0], x[0][1]))
    ]

    country_series = [
        {"country": country, "total_requests": total}
        for country, total in sorted(country_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    location_series = [
        {"location": location, "total_value": total}
        for location, total in sorted(location_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "dns_label_series": dns_label_series,
        "dns_daily_series": dns_daily_series,
        "daily_metric_series": daily_metric_series,
        "metric_totals": metric_totals,
        "intraday_series": intraday_series,
        "country_series": country_series,
        "location_series": location_series,
    }


def _build_dashboard(path: Path, dashboard_data: dict[str, list[dict[str, str | int | float]]], summary: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    # Script tag JSON must be raw JSON text (not HTML-escaped entities).
    # Escape only the script-closing sequence to keep embedding safe.
    payload_json = json.dumps(dashboard_data, ensure_ascii=True).replace("</", "<\\/")
    summary_json = json.dumps(summary, ensure_ascii=True).replace("</", "<\\/")

    html_content = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Cloudflare Collated Analytics</title>
  <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
  <style>
    :root {{
      --bg: #f5f6f8;
      --card: #ffffff;
      --ink: #14171f;
      --muted: #5c6374;
      --accent: #f38020;
      --accent-2: #0f766e;
      --border: #d9deea;
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at 0 0, #ffffff 0, #eef2ff 35%, var(--bg) 100%);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      gap: 16px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    h1 {{ margin: 0; font-size: 1.55rem; }}
    p {{ margin: 4px 0; color: var(--muted); }}
    .stat-row {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; }}
    .pill {{
      background: #fff7ed;
      border: 1px solid #fed7aa;
      color: #9a3412;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 0.85rem;
    }}
    .plot {{ min-height: 360px; }}
        .small-plot {{ min-height: 280px; }}
        .help {{ color: var(--muted); font-size: 0.9rem; margin-top: 8px; }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"card\">
      <h1>Cloudflare Collated Analytics</h1>
      <p>Persistent, de-duplicated history merged from multiple Cloudflare CSV exports.</p>
      <div id=\"stats\" class=\"stat-row\"></div>
    </section>
    <section class=\"card\">
            <h2>30-Day Trends (Cloudflare-style)</h2>
            <div id=\"uniqueVisitorsPlot\" class=\"small-plot\"></div>
            <div id=\"totalRequestsPlot\" class=\"small-plot\"></div>
            <p class=\"help\">These trends use day-level CSV rows (for example, "17 MAY") parsed into real dates.</p>
    </section>
        <section class=\"card\">
            <h2>DNS Daily Volume</h2>
            <div id=\"dnsDailyPlot\" class=\"plot\"></div>
        </section>
    <section class=\"grid\">
      <div class=\"card\">
        <h2>Country Requests (total)</h2>
        <div id=\"countryPlot\" class=\"plot\"></div>
      </div>
      <div class=\"card\">
        <h2>Location Values (total)</h2>
        <div id=\"locationPlot\" class=\"plot\"></div>
      </div>
    </section>
        <section class=\"card\" id=\"intradaySection\" style=\"display:none\">
            <h2>Intraday Pattern (Only if hourly buckets were exported)</h2>
            <div id=\"intradayPlot\" class=\"plot\"></div>
    </section>
  </div>

    <script id=\"dashboard-data\" type=\"application/json\">__DASHBOARD_PAYLOAD__</script>
    <script id=\"dashboard-summary\" type=\"application/json\">__DASHBOARD_SUMMARY__</script>
  <script>
    const data = JSON.parse(document.getElementById("dashboard-data").textContent);
    const summary = JSON.parse(document.getElementById("dashboard-summary").textContent);

    const statHost = document.getElementById("stats");
    const stats = [
      `Rows: ${summary.total_rows}`,
      `New Rows: ${summary.new_rows_in_batch}`,
      `Skipped Duplicates: ${summary.skipped_duplicates_in_batch}`,
      `Files Processed: ${summary.files_processed}`,
            `Schemas: ${Object.keys(summary.rows_by_schema || {}).length}`,
    ];
        for (const item of stats) {
      const span = document.createElement("span");
      span.className = "pill";
      span.textContent = item;
      statHost.appendChild(span);
        }

        const dailyGroups = new Map();
        for (const row of data.daily_metric_series || []) {
            if (!dailyGroups.has(row.metric)) dailyGroups.set(row.metric, []);
            dailyGroups.get(row.metric).push(row);
        }
        for (const rows of dailyGroups.values()) {
            rows.sort((a, b) => a.date.localeCompare(b.date));
        }

        function buildTrendPlot(divId, metric, label, color) {
            const rows = dailyGroups.get(metric) || [];
            const host = document.getElementById(divId);
            if (!rows.length) {
                host.textContent = `No day-level data for ${label}.`;
                return;
            }

            Plotly.newPlot(divId, [{
                type: "scatter",
                mode: "lines+markers",
                x: rows.map(r => r.date),
                y: rows.map(r => r.value),
                line: { width: 2, color },
                marker: { size: 6, color },
                fill: "tozeroy",
                fillcolor: color + "22",
                name: label,
            }], {
                title: label,
                margin: { t: 38, r: 16, b: 40, l: 48 },
                xaxis: { title: "Date" },
                yaxis: { title: "Value" },
                showlegend: false,
            }, {responsive: true});
        }

        buildTrendPlot("uniqueVisitorsPlot", "unique_visitors", "Unique Visitors", "#1d4ed8");
        buildTrendPlot("totalRequestsPlot", "total_requests", "Total Requests", "#f38020");

        const dnsDaily = data.dns_daily_series || [];
        if (dnsDaily.length) {
            Plotly.newPlot("dnsDailyPlot", [{
                type: "scatter",
                mode: "lines+markers",
                x: dnsDaily.map(r => r.date),
                y: dnsDaily.map(r => r.value),
                line: { width: 2, color: "#0f766e" },
                marker: { size: 5, color: "#0f766e" },
                name: "DNS Daily Volume",
            }], {
                margin: { t: 16, r: 16, b: 40, l: 48 },
                xaxis: { title: "Date" },
                yaxis: { title: "Count" },
                showlegend: false,
            }, {responsive: true});
        } else {
            document.getElementById("dnsDailyPlot").textContent = "No DNS daily data found.";
        }

    const topCountries = data.country_series.slice(0, 20);
    Plotly.newPlot("countryPlot", [{
      type: "bar",
      x: topCountries.map(r => r.country),
      y: topCountries.map(r => r.total_requests),
            marker: { color: "#f38020" }
        }], {
            margin: { t: 16, r: 16, b: 60, l: 48 },
            xaxis: { title: "Country" },
            yaxis: { title: "Total Requests" }
        }, {responsive: true});

    const topLocations = data.location_series.slice(0, 20);
    Plotly.newPlot("locationPlot", [{
      type: "bar",
      x: topLocations.map(r => r.location),
      y: topLocations.map(r => r.total_value),
            marker: { color: "#0f766e" }
        }], {
            margin: { t: 16, r: 16, b: 110, l: 48 },
            xaxis: { title: "Location", tickangle: -35 },
            yaxis: { title: "Total Value" }
        }, {responsive: true});

        const intraday = data.intraday_series || [];
        if (intraday.length) {
            document.getElementById("intradaySection").style.display = "block";
            const intradayMetric = intraday[0].metric;
            const intradayRows = intraday.filter(r => r.metric === intradayMetric);
            Plotly.newPlot("intradayPlot", [{
                type: "scatter",
                mode: "lines+markers",
                x: intradayRows.map(r => r.clock_time),
                y: intradayRows.map(r => r.avg_value),
                line: { width: 2, color: "#6d28d9" },
                marker: { size: 5, color: "#6d28d9" },
                name: intradayMetric,
            }], {
                margin: { t: 16, r: 16, b: 50, l: 48 },
                xaxis: { title: "Clock Time Bucket" },
                yaxis: { title: "Average Value" },
                showlegend: false,
            }, {responsive: true});
        }
  </script>
</body>
</html>
"""

    html_content = html_content.replace("{{", "{").replace("}}", "}")
    html_content = html_content.replace("__DASHBOARD_PAYLOAD__", payload_json)
    html_content = html_content.replace("__DASHBOARD_SUMMARY__", summary_json)

    path.write_text(html_content, encoding="utf-8")


def collate(input_path: Path, output_dir: Path, state_dir: Path, batch_name: str | None = None) -> dict[str, object]:
    csv_files, temp_dir = _collect_csv_paths(input_path)
    batch = batch_name or input_path.stem
    ingested_at = _now_utc_iso()

    try:
        fingerprint_file = state_dir / "fingerprints.txt"
        events_file = state_dir / "events.ndjson"

        known = _read_existing_fingerprints(fingerprint_file)
        run_seen: set[str] = set()

        new_rows: list[dict[str, str | int | float | None]] = []
        skipped_duplicates = 0
        unsupported_files: list[str] = []

        for csv_path in csv_files:
            anchor_date = _extract_anchor_date(csv_path.name)
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    unsupported_files.append(csv_path.name)
                    continue

                schema = detect_schema(reader.fieldnames)
                if not schema:
                    unsupported_files.append(csv_path.name)
                    continue

                for source_row in reader:
                    normalized = _normalize_row(
                        schema,
                        source_row,
                        source_name=csv_path.name,
                        anchor_date=anchor_date,
                    )
                    fp = _fingerprint(normalized)
                    if fp in known or fp in run_seen:
                        skipped_duplicates += 1
                        continue

                    run_seen.add(fp)
                    row = {
                        "ingested_at_utc": ingested_at,
                        "source_batch": batch,
                        "source_file": csv_path.name,
                        **normalized,
                    }
                    new_rows.append(row)

        known.update(run_seen)
        _write_fingerprints(fingerprint_file, known)
        _append_jsonl(events_file, new_rows)

        all_rows = _read_jsonl(events_file)
        all_rows.sort(
            key=lambda r: (
                str(r.get("schema", "")),
                str(r.get("label", "")),
                str(r.get("country", "")),
                str(r.get("location", "")),
                str(r.get("timestamp_utc", "")),
                str(r.get("clock_time", "")),
                str(r.get("value", "")),
            )
        )

        events_csv = output_dir / "cloudflare_events.csv"
        events_ndjson = output_dir / "cloudflare_events.ndjson"
        summary_file = output_dir / "cloudflare_summary.json"
        dashboard_file = output_dir / "cloudflare_dashboard.html"

        _materialize_csv(events_csv, all_rows)
        events_ndjson.write_text("\n".join(json.dumps(r, ensure_ascii=True, sort_keys=True) for r in all_rows) + "\n", encoding="utf-8")

        rows_by_schema: dict[str, int] = defaultdict(int)
        for row in all_rows:
            rows_by_schema[str(row.get("schema", "unknown"))] += 1

        summary: dict[str, object] = {
            "generated_at_utc": _now_utc_iso(),
            "input": str(input_path),
            "batch": batch,
            "files_processed": len(csv_files),
            "unsupported_files": unsupported_files,
            "new_rows_in_batch": len(new_rows),
            "skipped_duplicates_in_batch": skipped_duplicates,
            "total_rows": len(all_rows),
            "rows_by_schema": dict(sorted(rows_by_schema.items())),
            "outputs": {
                "events_csv": str(events_csv),
                "events_ndjson": str(events_ndjson),
                "summary_json": str(summary_file),
                "dashboard_html": str(dashboard_file),
                "state_fingerprints": str(fingerprint_file),
                "state_events_ndjson": str(events_file),
            },
        }

        dashboard_data = _aggregate_for_dashboard(all_rows)
        _build_dashboard(dashboard_file, dashboard_data, summary)
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

        return summary
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description="Collate and de-duplicate Cloudflare CSV exports")
    parser.add_argument("--input", required=True, help="Path to Cloudflare CSV zip archive or directory")
    parser.add_argument(
        "--output-dir",
        default="data/cloudflare/collated",
        help="Directory for materialized CSV/JSON/dashboard outputs",
    )
    parser.add_argument(
        "--state-dir",
        default="data/cloudflare/state",
        help="Directory for persistent de-duplication state files",
    )
    parser.add_argument(
        "--batch-name",
        default=None,
        help="Optional batch label stored in output rows",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    state_dir = Path(args.state_dir)

    if not input_path.exists():
        raise SystemExit(f"Input path not found: {input_path}")

    summary = collate(input_path=input_path, output_dir=output_dir, state_dir=state_dir, batch_name=args.batch_name)
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
