# 08 · Log Analyzer

A real command-line tool that parses web server logs, which can be large, and summarizes traffic and errors.

**Builds on 07:** dataclasses, type hints, tests.

## Concepts
- `argparse` for command-line arguments and flags
- Regular expressions (`re.compile`, named groups `(?P<name>...)`)
- Generators and `yield`, for processing huge files without loading them into memory
- Generator expressions
- `collections.Counter` and `defaultdict`
- `datetime.strptime`
- `sys.exit` with exit codes, and writing to `sys.stderr`

## Setup: generate test data
Write `generate_logs.py` that creates `access.log` with 100,000 lines in this format:
```
192.168.1.20 - - [18/Oct/2026:14:02:11 +0000] "GET /products/42 HTTP/1.1" 200 5123 0.084
```
Fields: IP, timestamp, method, path, protocol, status code, response bytes, response time in seconds. Use `random.choices` with weights so that most responses are 200 and a few are 404 or 500.

## Core requirements
Usage:
```
python analyze.py access.log [--top N] [--status CODE] [--since DATETIME] [--until DATETIME] [--format text|json]
```
1. `parse_lines(path)` is a **generator** that yields one `LogEntry` dataclass per line. Malformed lines are skipped and counted.
2. Filtering is also done with generators (`filter_status`, `filter_time`), chained together lazily.
3. The report includes:
   - total requests, and how many lines were malformed
   - requests per status code
   - the top N paths and top N IPs
   - average and 95th-percentile response time
   - requests per hour (a simple text histogram)
   - the paths producing the most 5xx errors
4. `--format json` prints the report as JSON so other programs can use it.
5. A missing file prints an error to stderr and exits with code 1.

## Done when
- [ ] Memory use stays flat on a 1-million-line file (the file is never read fully into a list)
- [ ] The regex uses named groups
- [ ] `python analyze.py --help` shows helpful descriptions for every option
- [ ] Tests cover parsing a valid line, a malformed line, and each filter

## Stretch goals
- `--follow` mode: keep reading new lines as they're appended, like `tail -f`.
- Detect suspicious IPs (more than X requests per minute).
- Accept `.gz` files transparently (the `gzip` module).
- Time your analyzer with `time.perf_counter` and try to make it faster.

## Automated checks
Write your own tests in `tests/`. The provided checks in `spec_tests/` import `analyze.py` and also run it as a command. They assume:
- `LogEntry` has the fields `ip`, `timestamp` (a timezone-aware `datetime`), `method`, `path`, `protocol`, `status` (int), `size` (int), and `response_time` (float).
- `parse_line(line)` returns a `LogEntry`, or `None` for a malformed line.
- `parse_lines(path, stats=None)` is a generator. If you pass it a dict, it stores the number of malformed lines in `stats["malformed"]`.
- `filter_status(entries, status)` and `filter_time(entries, since=None, until=None)` are generators. `since` is inclusive and `until` is exclusive.
- `build_report(entries, top=5)` returns a dict with these keys:
  - `total`
  - `status_counts`: `{200: 3, ...}`, keyed by int
  - `top_paths`, `top_ips`, and `top_error_paths`: lists of `(value, count)`, most common first, with ties sorted alphabetically
  - `avg_response_time` and `p95_response_time`: `0.0` when there are no entries
  - `requests_per_hour`: `{"2026-10-18 14:00": 3, ...}`
- p95 uses the nearest-rank method: sort the times and take the item at index `ceil(0.95 * n) - 1`.
- `--format json` prints the `build_report` dict as JSON, plus a `malformed` count. JSON turns the int status keys into strings.
- `--since` and `--until` accept ISO datetimes like `2026-10-18T14:00:00`. Treat datetimes without a timezone as UTC.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Explain in your own words why `sum(1 for _ in parse_lines(path))` uses almost no memory, while `len(list(parse_lines(path)))` does.
