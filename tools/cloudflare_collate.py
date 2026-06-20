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
SCHEMA_SINGLE_VALUE = "single_value"


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
    if h == ("value",):
        return SCHEMA_SINGLE_VALUE
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
        "uncached_request": "uncached_requests",
        "uncached_requests": "uncached_requests",
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

    if schema == SCHEMA_SINGLE_VALUE:
        metric = _metric_from_source_name(source_name, "single_value")
        return {
            "schema": schema,
            "metric": metric,
            "timestamp_utc": anchor_date.isoformat() + "T00:00:00Z",
            "date_utc": anchor_date.isoformat(),
            "clock_time": "",
            "label": "",
            "country": "",
            "location": "",
            "id_code": "",
            "value": _to_number(row.get("value", "")),
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


def _extract_anchor_date_str(source_name: str) -> str | None:
    """Return ISO date string from a dated filename, or None for UUID names."""
    if re.search(r"^[0-9a-f-]{36}\.csv$", source_name):
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})", source_name)
    return m.group(1) if m else None


def _aggregate_for_dashboard(rows: list[dict[str, str | int | float | None]]) -> dict[str, object]:
    # DNS label: aggregate by day for readability
    dns_by_label_day: dict[tuple[str, str], float] = defaultdict(float)
    dns_daily_total: dict[str, float] = defaultdict(float)

    # Daily dated metrics (unique_visitors, total_requests, etc.)
    daily_metrics: dict[tuple[str, str], float] = defaultdict(float)

    # Location snapshots: keyed by export_date for named files, else "undated"
    loc_snapshots: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    # Country: keyed by export_date
    country_by_date: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    # Coverage
    coverage: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        metric = str(row.get("metric", ""))
        value = row.get("value")
        if value is None:
            continue
        numeric = float(value)
        source_file = str(row.get("source_file", ""))
        export_date = _extract_anchor_date_str(source_file) or "undated"

        if metric == "dns_count_by_label":
            timestamp = str(row.get("timestamp_utc", ""))
            label = str(row.get("label", "")) or "(unlabeled)"
            if timestamp:
                day = timestamp[:10]
                dns_by_label_day[(label, day)] += numeric
                dns_daily_total[day] += numeric
                coverage["dns_queries"].append(day)

        elif metric == "location_value":
            location = str(row.get("location", "")) or "(unknown)"
            loc_snapshots[export_date][location] += numeric

        elif metric == "country_requests":
            country = str(row.get("country", "")) or "(unknown)"
            country_by_date[export_date][country] += numeric

        else:
            date_utc = str(row.get("date_utc", ""))
            if not date_utc:
                ts = str(row.get("timestamp_utc", ""))
                if re.match(r"^\d{4}-\d{2}-\d{2}T", ts):
                    date_utc = ts[:10]
            if date_utc:
                daily_metrics[(metric, date_utc)] += numeric
                coverage[metric].append(date_utc)

    # --- DNS label daily series: top 8 labels by total ---
    label_totals: dict[str, float] = defaultdict(float)
    for (label, _day), val in dns_by_label_day.items():
        label_totals[label] += val
    top_labels = [l for l, _ in sorted(label_totals.items(), key=lambda x: x[1], reverse=True)[:8]]

    dns_label_daily = []
    for label in top_labels:
        entries = sorted(
            [(day, val) for (lbl, day), val in dns_by_label_day.items() if lbl == label],
            key=lambda x: x[0],
        )
        dns_label_daily.append({
            "label": label,
            "dates": [e[0] for e in entries],
            "values": [e[1] for e in entries],
        })

    # --- DNS daily totals ---
    dns_daily_series = [
        {"date": d, "value": v}
        for d, v in sorted(dns_daily_total.items())
    ]

    # --- Daily metrics (visitors / requests / etc.) ---
    daily_metric_series = [
        {"metric": m, "date": d, "value": v}
        for (m, d), v in sorted(daily_metrics.items())
    ]

    # --- Location snapshots for comparison (named dates only) ---
    named_loc_dates = sorted(d for d in loc_snapshots if d != "undated")
    loc_all_totals: dict[str, float] = defaultdict(float)
    for d in named_loc_dates:
        for loc, v in loc_snapshots[d].items():
            loc_all_totals[loc] += v
    top_locs = [l for l, _ in sorted(loc_all_totals.items(), key=lambda x: x[1], reverse=True)[:15]]

    location_snapshot_chart = {
        "dates": named_loc_dates,
        "locations": top_locs,
        "series": [
            {
                "date": d,
                "values": [loc_snapshots[d].get(loc, 0) for loc in top_locs],
            }
            for d in named_loc_dates
        ],
    }

    # Cumulative location totals (all sources)
    all_loc_totals: dict[str, float] = defaultdict(float)
    for snap in loc_snapshots.values():
        for loc, v in snap.items():
            all_loc_totals[loc] += v
    location_series = [
        {"location": loc, "total_value": v}
        for loc, v in sorted(all_loc_totals.items(), key=lambda x: x[1], reverse=True)[:20]
    ]

    # --- Country: latest named date as primary ---
    named_country_dates = sorted(d for d in country_by_date if d != "undated")
    latest_country_date = named_country_dates[-1] if named_country_dates else None
    primary_country = dict(country_by_date.get(latest_country_date or "undated", {}))
    country_series = [
        {"country": c, "requests": v, "snapshot_date": latest_country_date or "all"}
        for c, v in sorted(primary_country.items(), key=lambda x: x[1], reverse=True)[:30]
    ]

    # --- Coverage summary ---
    coverage_items = []
    for metric_name in sorted(coverage):
        dates = sorted(set(coverage[metric_name]))
        if dates:
            coverage_items.append({
                "metric": metric_name,
                "first": dates[0],
                "last": dates[-1],
                "count": len(dates),
            })

    return {
        "dns_label_daily": dns_label_daily,
        "dns_daily_series": dns_daily_series,
        "daily_metric_series": daily_metric_series,
        "location_snapshot_chart": location_snapshot_chart,
        "location_series": location_series,
        "country_series": country_series,
        "coverage_summary": coverage_items,
    }


def _build_dashboard(path: Path, dashboard_data: dict[str, object], summary: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    # Script tag JSON must be raw JSON text (not HTML-escaped entities).
    # Escape only the script-closing sequence to keep embedding safe.
    payload_json = json.dumps(dashboard_data, ensure_ascii=True).replace("</", "<\\/")
    summary_json = json.dumps(summary, ensure_ascii=True).replace("</", "<\\/")

    html_content = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cloudflare Collated Analytics</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      --bg: #f2f4f8; --card: #ffffff; --ink: #14171f; --muted: #5c6374;
      --accent: #f38020; --accent2: #1d4ed8; --green: #0f766e; --border: #d9deea;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Segoe UI","Helvetica Neue",sans-serif; color: var(--ink); background: var(--bg); }
    .wrap { max-width: 1280px; margin: 0 auto; padding: 20px; display: grid; gap: 14px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; box-shadow: 0 4px 14px rgba(15,23,42,.06); }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    h1 { margin: 0 0 4px; font-size: 1.4rem; }
    h2 { margin: 0 0 10px; font-size: 1.05rem; color: var(--ink); }
    .sub { color: var(--muted); font-size: 0.85rem; margin: 0 0 10px; }
    .pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .pill { background: #fff7ed; border: 1px solid #fed7aa; color: #9a3412; border-radius: 999px; padding: 4px 10px; font-size: 0.82rem; }
    .pill.blue { background: #eff6ff; border-color: #bfdbfe; color: #1e40af; }
    .pill.green { background: #f0fdf4; border-color: #bbf7d0; color: #166534; }
    .plot { min-height: 300px; }
    .plot-lg { min-height: 380px; }
    .coverage-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    .coverage-table th { text-align: left; padding: 6px 10px; background: #f8fafc; border-bottom: 2px solid var(--border); }
    .coverage-table td { padding: 6px 10px; border-bottom: 1px solid var(--border); }
    .gap-note { color: #b45309; font-size: 0.82rem; margin-top: 4px; }
    @media (max-width: 860px) { .grid2 { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<div class="wrap">
  <section class="card">
    <h1>Cloudflare Collated Analytics &mdash; arboreum.net</h1>
    <p class="sub">Persistent, de-duplicated history from all Cloudflare CSV exports. Updated: __GENERATED_AT__</p>
    <div class="pills" id="headerPills"></div>
  </section>
  <section class="card">
    <h2>Data Coverage</h2>
    <table class="coverage-table" id="coverageTable"></table>
    <p class="gap-note" id="gapNote"></p>
  </section>
  <section class="card">
    <h2>Unique Visitors (daily)</h2>
    <p class="sub" id="uvSpan"></p>
    <div id="uvPlot" class="plot-lg"></div>
  </section>
  <section class="card">
    <h2>Total Requests (daily)</h2>
    <p class="sub" id="trSpan"></p>
    <div id="trPlot" class="plot-lg"></div>
  </section>
    <section class="card">
        <h2>Traffic Time Series (30-day evidence)</h2>
        <p class="sub">Daily values from the traffic timeseries export family. This is the Feb-Mar coverage you called out.</p>
        <div id="trafficSeriesPlot" class="plot-lg"></div>
    </section>
  <section class="card">
    <h2>DNS Queries by Label (Mar&ndash;Apr, top 8 labels)</h2>
    <p class="sub">Hourly DNS resolution counts aggregated to daily totals per hostname label.</p>
    <div id="dnsLabelPlot" class="plot-lg"></div>
  </section>
  <section class="card">
    <h2>DNS Data Center Snapshots</h2>
    <p class="sub">Queries per Cloudflare PoP &mdash; three named export dates compared side by side.</p>
    <div id="dcSnapshotPlot" class="plot-lg"></div>
  </section>
  <section class="grid2">
    <div class="card">
      <h2>Country Requests</h2>
      <p class="sub" id="countryNote"></p>
      <div id="countryPlot" class="plot"></div>
    </div>
    <div class="card">
      <h2>DNS Data Centers (cumulative)</h2>
      <p class="sub">Total queries per PoP across all ingested location snapshots.</p>
      <div id="locationPlot" class="plot"></div>
    </div>
  </section>
</div>
<script id="dashboard-data" type="application/json">__DASHBOARD_PAYLOAD__</script>
<script id="dashboard-summary" type="application/json">__DASHBOARD_SUMMARY__</script>
<script>
const data    = JSON.parse(document.getElementById('dashboard-data').textContent);
const summary = JSON.parse(document.getElementById('dashboard-summary').textContent);
const COLORS  = ['#1d4ed8','#f38020','#0f766e','#7c3aed','#dc2626','#0891b2','#65a30d','#db2777'];
const PLY     = Plotly;

const pills = [
  { label: `Total Rows: ${summary.total_rows}` },
  { label: `Unique Visitors: ${(data.daily_metric_series||[]).filter(r=>r.metric==='unique_visitors').length} days`, cls:'blue' },
  { label: `Total Requests: ${(data.daily_metric_series||[]).filter(r=>r.metric==='total_requests').length} days`, cls:'blue' },
  { label: `DNS Label Rows: ${(data.dns_label_daily||[]).reduce((s,t)=>s+t.dates.length,0)}`, cls:'green' },
  { label: `Location Snapshots: ${(data.location_snapshot_chart&&data.location_snapshot_chart.dates||[]).length} dates`, cls:'green' },
  { label: `Files Processed: ${summary.files_processed}` },
];
const ph = document.getElementById('headerPills');
pills.forEach(p => {
  const s = document.createElement('span');
  s.className = 'pill ' + (p.cls||'');
  s.textContent = p.label;
  ph.appendChild(s);
});

const cov = data.coverage_summary || [];
const ct  = document.getElementById('coverageTable');
ct.innerHTML = '<tr><th>Metric</th><th>Earliest</th><th>Latest</th><th>Days in store</th></tr>'
  + cov.map(c=>`<tr><td>${c.metric}</td><td>${c.first}</td><td>${c.last}</td><td>${c.count}</td></tr>`).join('');
document.getElementById('gapNote').textContent =
  'Note: May 15-16 are missing from unique_visitors and total_requests \u2014 neither 30-day export window covered those two dates.';

const byMetric = new Map();
(data.daily_metric_series||[]).forEach(r => {
  if (!byMetric.has(r.metric)) byMetric.set(r.metric,[]);
  byMetric.get(r.metric).push(r);
});
byMetric.forEach(rows => rows.sort((a,b)=>a.date.localeCompare(b.date)));

function trendPlot(divId, metric, labelText, color, spanElId) {
    const rows = byMetric.get(metric)||[];
    // Overlay phone-export daily_value rows for dates not in the named metric
    const namedDates = new Set(rows.map(r=>r.date));
    const extRows = (byMetric.get('daily_value')||[]).filter(r=>!namedDates.has(r.date));
    const allRows = [...extRows,...rows].sort((a,b)=>a.date.localeCompare(b.date));
    if (!allRows.length) { document.getElementById(divId).textContent='No data.'; return; }
    if (spanElId) document.getElementById(spanElId).textContent =
        `${allRows[0].date} \u2192 ${allRows[allRows.length-1].date}  `
        + `(named: ${rows.length} days + ${extRows.length} phone-export days)`;
    const traces = [];
    if (extRows.length) {
        traces.push({
            type:'scatter', mode:'lines+markers',
            x:extRows.map(r=>r.date), y:extRows.map(r=>r.value),
            line:{width:1.5,color,dash:'dot'}, marker:{size:4,color,symbol:'circle-open'},
            name:'Phone exports (unconfirmed metric)',
            hovertemplate:'%{x}: <b>%{y:,}</b><extra>phone export</extra>',
        });
    }
    traces.push({
        type:'scatter', mode:'lines+markers',
        x:rows.map(r=>r.date), y:rows.map(r=>r.value),
        line:{width:2,color}, marker:{size:5,color},
        fill:'tozeroy', fillcolor:color+'1a', name:labelText,
        hovertemplate:'%{x}: <b>%{y:,}</b><extra></extra>',
    });
    PLY.newPlot(divId, traces, {
        margin:{t:10,r:10,b:60,l:60},
        xaxis:{title:'Date',showgrid:true},
        yaxis:{title:labelText,tickformat:',d'},
        shapes:[
            {type:'line',x0:'2026-05-15',x1:'2026-05-15',y0:0,y1:1,yref:'paper',line:{color:'#dc2626',width:1,dash:'dot'}},
            {type:'line',x0:'2026-05-16',x1:'2026-05-16',y0:0,y1:1,yref:'paper',line:{color:'#dc2626',width:1,dash:'dot'}},
        ],
        annotations:[{x:'2026-05-16',y:0.98,yref:'paper',text:'data gap',showarrow:false,font:{color:'#dc2626',size:10},xanchor:'left'}],
        legend:{orientation:'h',y:-0.22},
    },{responsive:true});
}

trendPlot('uvPlot','unique_visitors','Unique Visitors','#1d4ed8','uvSpan');
trendPlot('trPlot','total_requests', 'Total Requests', '#f38020','trSpan');

const trafficRows = (byMetric.get('daily_value') || []).slice().sort((a,b)=>a.date.localeCompare(b.date));
if (trafficRows.length) {
    PLY.newPlot('trafficSeriesPlot', [{
        type:'scatter', mode:'lines+markers',
        x: trafficRows.map(r=>r.date),
        y: trafficRows.map(r=>r.value),
        line:{width:2,color:'#0f766e'}, marker:{size:5,color:'#0f766e'},
        fill:'tozeroy', fillcolor:'#0f766e1a',
        name:'Traffic Time Series',
        hovertemplate:'%{x}: <b>%{y:,}</b><extra></extra>',
    }], {
        margin:{t:10,r:10,b:50,l:60},
        xaxis:{title:'Date',showgrid:true},
        yaxis:{title:'Traffic Value',tickformat:',d'},
        showlegend:false,
    }, {responsive:true});
} else {
    document.getElementById('trafficSeriesPlot').textContent = 'No traffic timeseries data available.';
}

const dnsLabels = data.dns_label_daily||[];
if (dnsLabels.length) {
  PLY.newPlot('dnsLabelPlot',
    dnsLabels.map((s,i)=>({
      type:'scatter', mode:'lines+markers',
      x:s.dates, y:s.values, name:s.label,
      line:{width:2,color:COLORS[i%COLORS.length]}, marker:{size:4},
      hovertemplate:'%{x}: <b>%{y:,}</b><extra>'+s.label+'</extra>',
    })),
    { margin:{t:10,r:10,b:80,l:60}, xaxis:{title:'Date',showgrid:true},
      yaxis:{title:'DNS Queries (daily)',tickformat:',d'},
      legend:{orientation:'h',y:-0.28}, hovermode:'x unified' },
    {responsive:true}
  );
} else { document.getElementById('dnsLabelPlot').textContent='No DNS label data.'; }

const snap = data.location_snapshot_chart||{};
if ((snap.dates||[]).length) {
  PLY.newPlot('dcSnapshotPlot',
    (snap.series||[]).map((s,i)=>({
      type:'bar', name:s.date,
      x:snap.locations, y:s.values,
      marker:{color:COLORS[i%COLORS.length]},
      hovertemplate:'%{x}: <b>%{y:,}</b><extra>'+s.date+'</extra>',
    })),
    { barmode:'group', margin:{t:10,r:10,b:140,l:60},
      xaxis:{title:'Data Center',tickangle:-40},
      yaxis:{title:'DNS Queries',tickformat:',d'},
      legend:{title:{text:'Export date'}} },
    {responsive:true}
  );
} else { document.getElementById('dcSnapshotPlot').textContent='No snapshot data.'; }

const countries = data.country_series||[];
if (countries.length) {
  document.getElementById('countryNote').textContent =
    `Snapshot: ${countries[0]&&countries[0].snapshot_date||'all'} \u2014 top ${countries.length} countries`;
  PLY.newPlot('countryPlot',[{
    type:'bar', x:countries.map(r=>r.country), y:countries.map(r=>r.requests),
    marker:{color:'#f38020'}, hovertemplate:'%{x}: <b>%{y:,}</b><extra></extra>',
  }],{ margin:{t:10,r:10,b:60,l:60}, xaxis:{title:'Country'},
      yaxis:{title:'Requests',tickformat:',d'}, showlegend:false },{responsive:true});
}

const locations = data.location_series||[];
if (locations.length) {
  PLY.newPlot('locationPlot',[{
    type:'bar', x:locations.map(r=>r.location), y:locations.map(r=>r.total_value),
    marker:{color:'#0f766e'}, hovertemplate:'%{x}: <b>%{y:,}</b><extra></extra>',
  }],{ margin:{t:10,r:10,b:140,l:60}, xaxis:{title:'Data Center',tickangle:-40},
      yaxis:{title:'Total DNS Queries',tickformat:',d'}, showlegend:false },{responsive:true});
}
</script>
</body>
</html>
"""

    html_content = html_content.replace("__GENERATED_AT__", str(summary.get("generated_at_utc", "")))
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
