"""Sight (Major 55): the visual read path — converter, FileScope.read_media, the multimodal
inference payload, and capability-routed read handling in LocalWorld."""

from pathlib import Path

from src.familiar import visual
from src.familiar.file_scope import FileScope
from src.familiar.local_world import LocalWorld
from src.inference.client import InferenceClient, model_accepts_images

# A minimal valid 1-page PDF with no extractable text — pdfium treats it as scanned.
_SCANNED_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 60 40]>>endobj\nxref\n0 4\n0000000000 65535 f \n"
    b"0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n164\n%%EOF\n"
)


def _png(width: int = 1, height: int = 1) -> bytes:
    """A real, tiny PNG built by our own stdlib encoder — a red pixel."""
    return visual._png_encode(width, height, 3, b"\xff\x00\x00" * (width * height), width * 3)


# --- the converter --------------------------------------------------------------

def test_kind_classification_by_ext_and_magic():
    assert visual.kind_of("x.png", b"") == "image"
    assert visual.kind_of("x.PDF", b"") == "pdf"
    assert visual.kind_of("noext", _png()) == "image"          # sniffed from magic
    assert visual.kind_of("noext", _SCANNED_PDF) == "pdf"
    assert visual.kind_of("notes.md", b"hello") is None


def test_image_data_url_round_trips_mime_and_base64():
    url = visual.image_data_url("pinto.jpg", b"\xff\xd8\xff\xe0junk")
    assert url.startswith("data:image/jpeg;base64,")


def test_png_encoder_is_valid_and_dimensioned():
    import struct
    raw = _png(3, 2)
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", raw[16:24])
    assert (w, h) == (3, 2)


def test_scanned_pdf_renders_for_vision_not_for_text_only():
    seen = visual.to_perception("scan.pdf", _SCANNED_PDF, want_images=True)
    assert seen["kind"] == "pdf" and seen["scanned"] == 1 and len(seen["images"]) == 1
    assert seen["images"][0].startswith("data:image/png;base64,")
    blind = visual.to_perception("scan.pdf", _SCANNED_PDF, want_images=False)
    assert blind["images"] == [] and "cannot see" in blind["note"]


def test_image_perception_is_honest_for_text_only_minds():
    assert visual.to_perception("p.png", _png(), want_images=True)["images"]      # a vision mind sees it
    blind = visual.to_perception("p.png", _png(), want_images=False)
    assert blind["images"] == [] and "cannot see" in blind["note"]               # a text-only mind is told, not faked


# --- FileScope.read_media (the capability guards) -------------------------------

def _scope(tmp: Path) -> tuple[FileScope, Path]:
    root = tmp / "scope"
    root.mkdir(parents=True, exist_ok=True)
    (root / "pic.png").write_bytes(_png())
    (root / "doc.pdf").write_bytes(_SCANNED_PDF)
    (root / "notes.md").write_text("just text")
    (root / ".env").write_text("SECRET=shh")
    return FileScope(read_roots=[str(root)]), root


def test_read_media_allows_image_and_pdf(tmp_path: Path):
    fs, _ = _scope(tmp_path)
    img = fs.read_media("pic.png")
    assert img["ok"] and img["kind"] == "image" and isinstance(img["data"], (bytes, bytearray))
    pdf = fs.read_media("doc.pdf")
    assert pdf["ok"] and pdf["kind"] == "pdf"


def test_read_media_still_denies_secrets_and_non_visual(tmp_path: Path):
    fs, _ = _scope(tmp_path)
    assert fs.read_media(".env")["ok"] is False        # the secret default-deny survives the relaxed binary check
    assert fs.read_media("notes.md")["reason"] == "not_visual"
    assert fs.read_media("nope.png")["reason"] in ("not_found", "outside_scope")


# --- the multimodal inference payload -------------------------------------------

def test_model_accepts_images_is_conservative():
    assert model_accepts_images("anthropic/claude-sonnet-4.5") is True
    assert model_accepts_images("google/gemini-3-flash-preview") is True
    assert model_accepts_images("mistralai/mistral-large") is False   # text line, not Pixtral
    assert model_accepts_images("deepseek/deepseek-chat-v3.1") is False
    assert model_accepts_images("some/unknown-model") is False


async def test_complete_builds_multimodal_array_only_when_images_present():
    captured: dict = {}

    client = InferenceClient(base_url="http://x", api_key="k", default_model="m")

    async def _fake_post(path, payload, **kw):
        captured["payload"] = payload
        return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    client._post_with_retry = _fake_post  # type: ignore[assignment]

    await client.complete("sys", "look", images=["data:image/png;base64,AAAA"])
    content = captured["payload"]["messages"][1]["content"]
    assert isinstance(content, list) and content[0]["type"] == "text" and content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")

    await client.complete("sys", "just text")  # no images -> unchanged flat-string path
    assert captured["payload"]["messages"][1]["content"] == "just text"
    await client.close()


# --- capability-routed reads in LocalWorld --------------------------------------

def _world(tmp: Path, *, vision: bool) -> LocalWorld:
    fs, _ = _scope(tmp)
    return LocalWorld(home_dir=tmp / "home", file_scope=fs, vision=vision)


async def test_vision_world_sees_image_and_holds_it(tmp_path: Path):
    w = _world(tmp_path, vision=True)
    r = await w.post_action("s", "read pic.png")
    assert "You can see it now" in r.narrative
    assert len(w.pending_images()) == 1 and w.pending_images()[0].startswith("data:image/png;base64,")


async def test_text_only_world_notes_image_but_holds_nothing(tmp_path: Path):
    w = _world(tmp_path, vision=False)
    r = await w.post_action("s", "read pic.png")
    assert "can't see it" in r.narrative
    assert w.pending_images() == []


async def test_reading_something_else_clears_the_held_image(tmp_path: Path):
    w = _world(tmp_path, vision=True)
    await w.post_action("s", "read pic.png")
    assert w.pending_images()
    await w.post_action("s", "read notes.md")   # a plain text read
    assert w.pending_images() == []
