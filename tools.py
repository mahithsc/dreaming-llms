import os
import re
import signal
import selectors
import subprocess
import time
import glob as globlib

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"


def read(args):
    lines = open(args["path"]).readlines()
    offset = args.get("offset", 0)
    limit = args.get("limit", len(lines))
    selected = lines[offset : offset + limit]
    return "".join(f"{offset + idx + 1:4}| {line}" for idx, line in enumerate(selected))


def write(args):
    with open(args["path"], "w") as f:
        f.write(args["content"])
    return "ok"

def edit(args):
    text = open(args["path"]).read()
    old, new = args["old"], args["new"]
    if old not in text:
        return "error: old_string not found"
    count = text.count(old)
    if not args.get("all") and count > 1:
        return f"error: old_string appears {count} times, must be unique (use all=true)"
    replacement = (
        text.replace(old, new) if args.get("all") else text.replace(old, new, 1)
    )
    with open(args["path"], "w") as f:
        f.write(replacement)
    return "ok"


def glob(args):
    pattern = (args.get("path", ".") + "/" + args["pat"]).replace("//", "/")
    files = globlib.glob(pattern, recursive=True)
    files = sorted(
        files,
        key=lambda f: os.path.getmtime(f) if os.path.isfile(f) else 0,
        reverse=True,
    )
    return "\n".join(files) or "none"


def grep(args):
    pattern = re.compile(args["pat"])
    hits = []
    for filepath in globlib.glob(args.get("path", ".") + "/**", recursive=True):
        try:
            for line_num, line in enumerate(open(filepath), 1):
                if pattern.search(line):
                    hits.append(f"{filepath}:{line_num}:{line.rstrip()}")
        except Exception:
            pass
    return "\n".join(hits[:50]) or "none"


def bash(args):
    timeout = float(args.get("timeout", 30))
    proc = subprocess.Popen(
        args["cmd"], shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=False,
        start_new_session=True,
    )
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    output_parts = []
    pending = ""
    deadline = time.monotonic() + timeout
    timed_out = False

    def flush_complete_lines():
        nonlocal pending
        while "\n" in pending:
            line, pending = pending.split("\n", 1)
            print(f"  {DIM}│ {line}{RESET}", flush=True)

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break

            events = selector.select(timeout=min(0.2, remaining))
            if events:
                chunk = os.read(proc.stdout.fileno(), 4096)
                if chunk:
                    text = chunk.decode("utf-8", errors="replace")
                    output_parts.append(text)
                    pending += text
                    flush_complete_lines()

            if proc.poll() is not None:
                while True:
                    chunk = os.read(proc.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    text = chunk.decode("utf-8", errors="replace")
                    output_parts.append(text)
                    pending += text
                    flush_complete_lines()
                break
    finally:
        selector.unregister(proc.stdout)
        selector.close()

    if timed_out and proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()

        # Grab any trailing bytes emitted while the process was shutting down.
        while True:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            output_parts.append(text)
            pending += text
            flush_complete_lines()

        output_parts.append(f"\n(timed out after {timeout:g}s)")

    if pending:
        print(f"  {DIM}│ {pending.rstrip()}{RESET}", flush=True)

    return "".join(output_parts).strip() or "(empty)"