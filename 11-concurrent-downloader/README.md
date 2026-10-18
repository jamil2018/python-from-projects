# 11 · Concurrent Downloader

Download many files at once, first with threads and then with `asyncio`, and measure the speedup.

**Builds on:** 08 (CLI and generators), 09 (HTTP and error handling).

## Concepts
- I/O-bound vs. CPU-bound work, and the GIL
- `concurrent.futures.ThreadPoolExecutor`, `as_completed`
- Thread safety, and `threading.Lock` for shared counters
- `async` / `await`, `asyncio.gather`, `asyncio.Semaphore`
- An async HTTP client (`httpx.AsyncClient` or `aiohttp`)
- Streaming downloads in chunks
- Timing with `time.perf_counter`
- Decorators (write a `@timed` decorator)

## Setup
Create `urls.txt` with 20–50 URLs of small files. For example, `https://picsum.photos/seed/1/800/600`, `/seed/2/...` and so on, or public-domain text from Project Gutenberg.

```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install httpx pytest
```

## Core requirements
```
python download.py urls.txt --out downloads/ --mode sequential|threads|async --workers 8
```
1. **Three implementations** with the same interface:
   - `download_sequential(urls, out_dir)`
   - `download_threaded(urls, out_dir, workers)`
   - `download_async(urls, out_dir, concurrency)`
2. Download in chunks to disk (never hold a whole file in memory).
3. Derive a safe, unique filename from each URL.
4. One failing URL must not stop the others. Collect the failures and report them at the end.
5. Show progress, for example `[12/40] done, 1 failed`. The counter has to be correct under threads (use a `Lock`).
6. Limit concurrency: at most `--workers` downloads at once, using an `asyncio.Semaphore` in async mode.
7. Write a `@timed` decorator and use it to print how long each mode took.
8. Skip files that already exist unless `--force` is given.

## Experiment
Run all three modes on the same list and fill in this table in a `RESULTS.md` file:

| Mode | Workers | Time (s) |
|------|---------|----------|
| sequential | 1 | |
| threads | 4 | |
| threads | 16 | |
| async | 16 | |

Then write a CPU-heavy task (for example, computing primes up to 5 million in chunks) and compare `ThreadPoolExecutor` with `ProcessPoolExecutor`. Explain the difference you see.

## Done when
- [ ] All three modes produce identical files
- [ ] Failures are reported, not raised
- [ ] The progress counter is correct with 32 threads
- [ ] `RESULTS.md` explains *why* threads helped for downloads but not for the prime computation

## Stretch goals
- Retry with backoff, and resume partial downloads using HTTP `Range` headers.
- Verify files against a SHA-256 checksum (`hashlib`).
- A live progress bar (write your own, or use `rich.progress`).

## Automated checks
The checks in `spec_tests/` start a small web server on your own machine (`127.0.0.1`), so they don't need the internet. They import `download.py` and also run it as a command. They assume:
- `download_sequential(urls, out_dir, force=False)` and `download_threaded(urls, out_dir, workers, force=False)` are normal functions.
- `download_async(urls, out_dir, concurrency, force=False)` is an `async def`. Run it with `asyncio.run`.
- All three return a `DownloadReport` with the attributes `succeeded` (a list of URLs), `failed` (a dict of URL to error message), and `skipped` (a list of URLs).
- A non-2xx status code counts as a failure.
- `safe_filename(url) -> str` is deterministic. It uses only letters, digits, `.`, `_`, and `-`, and gives different names to different URLs.
- After each URL finishes, print a progress line containing `[done/total]`, for example `[12/40] done, 1 failed`. Every number from 1 to the total appears exactly once.
- `timed` is a decorator that keeps the wrapped function's name (`functools.wraps`), returns its result, and prints a line containing that name and `took`.
- The command exits with code `1` if any download failed, and `0` otherwise.

```powershell
python -m pytest spec_tests -v
```

## Reflect
When would you choose threads, async, or processes? Write one sentence for each.
