#!/usr/bin/env python3
"""Preview the whole stable of familiars in a browser, no Tauri toolchain needed.

Serves the ui/ folder and three endpoints over the familiar root (the dir holding
each familiar's home folder):
  GET  /roster            -> [{name, mood, awake, ...}] for every familiar found
  GET  /state?who=<name>  -> that familiar's live state.json
  GET  /given?who=<name>  -> files already placed in workshop/given/<shelf>/
  GET  /given-file?who=<name>&path=<rel> -> text preview for a given file
  POST /whisper?who=<name>-> appends {ts, text} to that familiar's whispers.jsonl
  POST /give?who=<name>   -> optional local-only upload into workshop/given/<shelf>/ + given.jsonl

Run the familiars (scripts/familiar.py, or familiar/wake-all.sh) and this, then
open http://localhost:8777 and switch between them in the roster.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
UI = HERE / "ui"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ENABLE_WRITES = os.environ.get("STABLE_PORTRAIT_ENABLE_WRITES") == "1"


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _exchange(home: Path, n: int = 40) -> list[dict]:
    """The live back-and-forth, read straight from the durable record (whispers.jsonl + voice.jsonl) —
    NOT the once-per-tick state.json snapshot. This is what lets the portrait show a just-sent whisper
    on the next poll, and survive a reload: the keeper's words are on disk the instant they are sent,
    so the conversation never waits on the daemon's 30s tick to surface. Shape mirrors the daemon's
    own `_recent_exchange` so the UI renders it unchanged."""
    turns: list[dict] = []
    for w in _read_jsonl(home / "whispers.jsonl"):
        if w.get("text"):
            turns.append({"who": "you", "kind": "whisper", "text": str(w["text"]).strip(), "ts": str(w.get("ts") or "")})
    for v in _read_jsonl(home / "voice.jsonl"):
        if v.get("kind") in ("speak", "do") and v.get("text"):
            turns.append({"who": "her", "kind": v["kind"], "text": str(v["text"]).strip(), "ts": str(v.get("ts") or "")})

    def _key(t: dict) -> float:
        try:
            return datetime.fromisoformat(t["ts"]).timestamp()
        except (ValueError, TypeError):
            return 0.0

    turns.sort(key=_key)
    return turns[-n:]


def _safe_upload_name(raw: str) -> str:
    name = str(raw or "").replace("\\", "/").split("/")[-1]
    name = "".join(ch for ch in name if ch not in "\r\n\x00").strip()
    name = re.sub(r"\s+", " ", name)
    if not name or name in {".", ".."}:
        return "gift"
    return name[:180]


def _safe_shelf(raw: str) -> str:
    shelf = str(raw or "inbox").replace("\\", "/").split("/")[-1].strip().lower()
    shelf = re.sub(r"[^a-z0-9_-]+", "-", shelf).strip("-_")
    return shelf[:60] if shelf else "inbox"


def _unique_dest(folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    safe = _safe_upload_name(name)
    path = folder / safe
    if not path.exists():
        return path
    p = Path(safe)
    stem = p.stem or "gift"
    suffix = p.suffix
    idx = 2
    while True:
        candidate = folder / f"{stem}-{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def _dormant(home: Path) -> bool:
    """A familiar laid to the side: present and preserved on disk, but not woken or shown."""
    try:
        return bool(json.loads((home / "familiar.json").read_text(encoding="utf-8")).get("dormant"))
    except (OSError, ValueError):
        return False


def _familiars(root: Path) -> list[str]:
    if not root.exists():
        return []
    out = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name != "portrait" and (child / "identity").is_dir() and not _dormant(child):
            out.append(child.name)
    return out


def _roster(root: Path) -> list[dict]:
    now = datetime.now(timezone.utc)
    roster = []
    for name in _familiars(root):
        state_path = root / name / "state.json"
        entry = {"who": name, "name": name.replace("_", " ").title(), "mood": "asleep", "awake": False, "live": False}
        if state_path.exists():
            try:
                st = json.loads(state_path.read_text(encoding="utf-8"))
                age = (now - datetime.fromisoformat(st["ts"])).total_seconds() if st.get("ts") else 1e9
                entry.update(
                    {
                        "name": st.get("name") or entry["name"],
                        "mood": st.get("mood") or "—",
                        "awake": bool(st.get("awake")),
                        "arousal": float(st.get("arousal") or 0.0),
                        "wakefulness": float(st.get("wakefulness") or 1.0),
                        "local_time": st.get("local_time") or "",
                        "live": age < 150,
                    }
                )
            except (json.JSONDecodeError, OSError, ValueError):
                pass
        roster.append(entry)
    return roster


def _given_shelves(home: Path) -> list[dict]:
    given = home / "workshop" / "given"
    if not given.exists():
        return []
    shelves: dict[str, list[dict]] = {}
    for path in sorted(given.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(given)
        except ValueError:
            continue
        parts = rel.parts
        shelf = parts[0] if len(parts) > 1 else "inbox"
        name = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
        shelves.setdefault(shelf, []).append({"name": name, "path": rel.as_posix(), "bytes": path.stat().st_size})
    return [{"shelf": shelf, "files": files} for shelf, files in sorted(shelves.items())]


def make_handler(root: Path):
    def safe_home(who: str) -> Path | None:
        who = (who or "").strip()
        if not who or who in _familiars(root):
            return (root / who) if who else None
        return None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body: bytes, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _who(self):
            q = parse_qs(urlparse(self.path).query)
            who = (q.get("who") or [""])[0]
            return safe_home(who) or (root / (_familiars(root)[0] if _familiars(root) else ""))

        def _multipart(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}, []
            if length > MAX_UPLOAD_BYTES:
                raise ValueError("upload too large")
            ctype = self.headers.get("Content-Type") or ""
            if "multipart/form-data" not in ctype:
                raise ValueError("expected multipart/form-data")
            body = self.rfile.read(length)
            head = f"Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
            msg = BytesParser(policy=email_policy).parsebytes(head + body)
            fields: dict[str, str] = {}
            files: list[tuple[str, bytes]] = []
            parts = msg.iter_parts() if msg.is_multipart() else []
            for part in parts:
                if part.get_content_disposition() != "form-data":
                    continue
                name = str(part.get_param("name", header="content-disposition") or "")
                filename = part.get_filename()
                data = part.get_payload(decode=True) or b""
                if filename:
                    files.append((filename, data))
                elif name:
                    fields[name] = data.decode("utf-8", errors="replace")
            return fields, files

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/roster":
                self._send(200, json.dumps(_roster(root)).encode("utf-8"))
                return
            if path == "/state":
                sp = self._who() / "state.json"
                if sp.exists():
                    self._send(200, sp.read_bytes())
                else:
                    self._send(200, json.dumps({"name": "—", "mood": "asleep", "felt_sense": "(not yet woken)", "awake": False}).encode("utf-8"))
                return
            if path == "/exchange":
                # The conversation read live from the record, so a sent whisper (and her replies) surface
                # on the next poll instead of waiting on the 30s tick — and survive a page reload.
                self._send(200, json.dumps(_exchange(self._who()), ensure_ascii=False).encode("utf-8"))
                return
            if path == "/given":
                self._send(200, json.dumps(_given_shelves(self._who()), ensure_ascii=False).encode("utf-8"))
                return
            if path == "/given-file":
                q = parse_qs(urlparse(self.path).query)
                rel = (q.get("path") or [""])[0]
                given = (self._who() / "workshop" / "given").resolve()
                target = (given / rel).resolve()
                if rel and given in target.parents and target.is_file():
                    self._send(200, target.read_bytes(), "text/plain; charset=utf-8")
                else:
                    self._send(404, b"not found", "text/plain")
                return
            if path == "/artifact":
                # full text of one workshop artifact (e.g. the journal), so the rail's
                # last-excerpt isn't the only view. Name sanitized; confined to workshop/.
                q = parse_qs(urlparse(self.path).query)
                name = "".join(c for c in (q.get("name") or [""])[0] if c.isalnum() or c in "-_")
                wsdir = (self._who() / "workshop").resolve()
                f = (wsdir / f"{name}.md").resolve()
                if name and wsdir in f.parents and f.is_file():
                    self._send(200, f.read_bytes(), "text/plain; charset=utf-8")
                else:
                    self._send(404, b"not found", "text/plain")
                return
            rel = path.lstrip("/") or "index.html"
            target = (UI / rel).resolve()
            if UI in target.parents and target.is_file():
                ctype = "text/html" if target.suffix == ".html" else "text/css" if target.suffix == ".css" else "application/javascript" if target.suffix == ".js" else "application/octet-stream"
                self._send(200, target.read_bytes(), ctype)
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):
            path = urlparse(self.path).path
            if path == "/give":
                if not ENABLE_WRITES:
                    self._send(
                        403,
                        json.dumps(
                            {
                                "ok": False,
                                "error": "browser file gifts are disabled; use the native app or set STABLE_PORTRAIT_ENABLE_WRITES=1 for a trusted local session",
                            }
                        ).encode("utf-8"),
                    )
                    return
                try:
                    fields, files = self._multipart()
                except ValueError as exc:
                    self._send(400, json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"))
                    return
                if not files:
                    self._send(400, b'{"ok":false,"error":"no files"}')
                    return
                home = self._who()
                given = home / "workshop" / "given"
                ts = datetime.now().astimezone().isoformat()
                note = str(fields.get("note") or "").strip()
                shelf = _safe_shelf(fields.get("shelf") or "inbox")
                rouse = str(fields.get("rouse") or "").lower() in {"1", "true", "yes", "on"}
                saved = []
                for filename, data in files:
                    dest = _unique_dest(given / shelf, filename)
                    dest.write_bytes(data)
                    rel = dest.relative_to(given).as_posix()
                    saved.append({"file": rel, "bytes": len(data), "shelf": shelf})
                    _append_jsonl(home / "given.jsonl", {"ts": ts, "file": rel, "note": note, "shelf": shelf})
                if rouse:
                    names = ", ".join(item["file"] for item in saved)
                    say = note or f"I left you {names} in your given folder."
                    _append_jsonl(home / "whispers.jsonl", {"ts": ts, "text": say})
                self._send(200, json.dumps({"ok": True, "files": saved, "roused": rouse}, ensure_ascii=False).encode("utf-8"))
                return
            if path != "/whisper":
                self._send(404, b"not found", "text/plain")
                return
            length = int(self.headers.get("Content-Length") or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                text = str(payload.get("text") or "").strip()
            except (json.JSONDecodeError, ValueError):
                text = ""
            if text:
                line = json.dumps({"ts": datetime.now().astimezone().isoformat(), "text": text}, ensure_ascii=False)
                with (self._who() / "whispers.jsonl").open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            self._send(200, b'{"ok":true}')

    return Handler


def main() -> None:
    p = argparse.ArgumentParser(description="Browser preview for the stable of familiars.")
    p.add_argument("--root", default="..", help="dir holding the familiar home folders (default: familiar/)")
    p.add_argument("--port", type=int, default=8777)
    args = p.parse_args()
    root = (HERE / args.root).resolve() if not Path(args.root).is_absolute() else Path(args.root)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(root))
    fams = _familiars(root)
    print(f"· the stable at http://localhost:{args.port}  ·  familiars: {', '.join(fams) or '(none found)'}  (root: {root})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
