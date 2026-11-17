"""QA: reconcile Producer event_ids against Elasticsearch documents.

Usage (from repo root):
    .\\.venv\\Scripts\\python.exe .\\scripts\\qa\\reconcile_events.py docs\\qa\\evidence\\producer_run*.log

Reads the "Da gui: <event_id> | partition=N | offset=M" lines that
ingestion/test_producer_v2.py prints, fetches each document from
Elasticsearch by _id, and reports:
  - missing ids (sent but not in ES)
  - whether _id == event_id
  - required fields present
  - latency processed_at - collected_at (seconds; second-level precision)
It only reads from Elasticsearch; it never writes or deletes.
"""
import glob
import json
import re
import statistics
import sys
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import urlopen

ES_URL = "http://localhost:9200"
INDEX = "social_events_v1"
REQUIRED = ["event_id", "platform", "content_type", "text", "language",
            "created_at", "collected_at", "processed_at", "engagement",
            "kafka_topic", "kafka_partition", "kafka_offset"]
LINE_RE = re.compile(r"Da gui: (\S+) \| partition=(\d+) \| offset=(\d+)")


def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch(doc_id):
    try:
        with urlopen(f"{ES_URL}/{INDEX}/_doc/{doc_id}", timeout=10) as r:
            return json.load(r)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def percentile(values, p):
    """Nearest-rank percentile."""
    ordered = sorted(values)
    k = max(0, int(-(-p * len(ordered) // 100)) - 1)
    return ordered[k]


def main(patterns):
    sent = []
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    m = LINE_RE.search(line)
                    if m:
                        sent.append((path, m.group(1), int(m.group(2)), int(m.group(3))))

    print(f"Producer events parsed: {len(sent)} "
          f"(unique ids: {len({s[1] for s in sent})})")
    print("run_log | event_id | partition/offset (producer) | found | _id==event_id "
          "| partition/offset (ES) | missing_fields | latency_s")
    latencies, missing = [], []
    for path, eid, part, off in sent:
        doc = fetch(eid)
        if doc is None:
            missing.append(eid)
            print(f"{path} | {eid} | {part}/{off} | NO | - | - | - | -")
            continue
        src = doc["_source"]
        miss = [f for f in REQUIRED if f not in src]
        lat = (parse_ts(src["processed_at"]) - parse_ts(src["collected_at"])).total_seconds()
        latencies.append(lat)
        print(f"{path} | {eid} | {part}/{off} | YES | {doc['_id'] == src.get('event_id')} "
              f"| {src.get('kafka_partition')}/{src.get('kafka_offset')} "
              f"| {miss or 'none'} | {lat:.0f}")

    print(f"\nMissing in ES: {len(missing)} {missing}")
    if latencies:
        print(f"Latency processed_at-collected_at (s): n={len(latencies)} "
              f"min={min(latencies):.0f} max={max(latencies):.0f} "
              f"mean={statistics.mean(latencies):.2f} "
              f"p50={percentile(latencies, 50):.0f} p95={percentile(latencies, 95):.0f}")
        print("NOTE: second-level timestamps and n is small; not a benchmark.")


if __name__ == "__main__":
    main(sys.argv[1:] or ["docs/qa/evidence/producer_run*.log"])
