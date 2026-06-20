# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Visual reads: turn an in-scope image or PDF into something a mind can perceive.

FileScope refuses arbitrary binary by construction — its bytes would otherwise reach a
prompt blind. Images and PDFs are the one exception worth making: a vision-capable model
can genuinely *see* an image, and a PDF's text is legible to any model at all. This module
is the converter between a file's bytes (already root- and ignore-cleared by FileScope) and
a *perception*:

  - **image** -> a base64 ``data:`` URL (an image block) for vision-capable models
  - **PDF**   -> extracted text (legible to *every* model) **plus** rendered page images for
                 pages that are scanned — i.e. carry no extractable text — for vision models only

This honours the heterogeneity of the stable: a digital PDF becomes text every mind can read;
a scanned PDF becomes page-images only the vision minds (Cinder, Maker, Mason) can use, and a
text-only mind (Gaston, Skein) gets an honest "a scan I can't read as text" rather than a faked
description — the quiet guarantee at the model layer.

Nothing here touches the filesystem; it works on bytes FileScope already handed over. The one
heavy dependency, ``pypdfium2``, is imported lazily (only a PDF read pays it) and is the only
thing that rasterizes a scanned page. PNG encoding of a rendered page is stdlib ``zlib`` —
Pillow and numpy are deliberately *not* pulled in.
"""

from __future__ import annotations

import base64
import os
import struct
import zlib
from typing import Any

# Recognised visual types. Extension is the primary signal; a magic-byte sniff backs it up so a
# mislabelled file still classifies (and a non-visual file with a visual extension is caught).
_IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

# Bounds — a familiar's perception is not a place to load a 200-page scan or a 50 MB raster.
_MAX_PDF_PAGES = 12          # pages we extract text from
_MAX_RENDERED_PAGES = 5      # of those, how many scanned pages we rasterize (cost ceiling)
_RENDER_SCALE = 2.0          # ~150 dpi; vision models downscale anyway
_SCANNED_TEXT_FLOOR = 16     # a page with fewer non-space chars than this is treated as scanned


def kind_of(name: str, data: bytes = b"") -> str | None:
    """Classify a file as ``"image"``, ``"pdf"``, or ``None`` (not a visual type), by
    extension first and a magic-byte sniff second."""
    ext = os.path.splitext(str(name or ""))[1].lower()
    if ext == ".pdf" or data[:5] == b"%PDF-":
        return "pdf"
    if ext in _IMAGE_MIME:
        return "image"
    # extension lied or was absent — sniff the common image magics
    if data[:8] == b"\x89PNG\r\n\x1a\n" or data[:3] == b"\xff\xd8\xff" or data[:6] in (b"GIF87a", b"GIF89a") or (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        return "image"
    return None


def _image_mime(name: str, data: bytes) -> str:
    ext = os.path.splitext(str(name or ""))[1].lower()
    if ext in _IMAGE_MIME:
        return _IMAGE_MIME[ext]
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def image_data_url(name: str, data: bytes) -> str:
    """A ``data:<mime>;base64,...`` URL for an image file's raw bytes — the form an
    OpenAI-compatible ``image_url`` content block wants."""
    return f"data:{_image_mime(name, data)};base64," + base64.b64encode(data).decode("ascii")


# --- a minimal, dependency-free PNG encoder for rendered PDF pages -----------------

def _png_encode(width: int, height: int, channels: int, raw: bytes, src_stride: int) -> bytes:
    """Encode tightly-or-padded RGB/RGBA pixel rows as a PNG (stdlib zlib only). ``raw`` is the
    pdfium bitmap buffer with R-first byte order (``rev_byteorder=True``); ``src_stride`` is its
    real row stride (may exceed ``width*channels`` by padding, which we drop)."""
    color_type = 6 if channels == 4 else 2  # 6 = truecolour+alpha, 2 = truecolour
    row_len = width * channels
    scan = bytearray()
    for y in range(height):
        off = y * src_stride
        scan.append(0)  # filter type 0 (none) for each scanline
        scan += raw[off:off + row_len]

    def _chunk(tag: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    idat = zlib.compress(bytes(scan), 6)
    return sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def _render_page_png(page: Any) -> bytes:
    """Rasterize one pdfium page to PNG bytes (RGB/RGBA), via the stdlib encoder."""
    bmp = page.render(scale=_RENDER_SCALE, rev_byteorder=True)  # rev_byteorder -> R-first (RGB/RGBA)
    return _png_encode(bmp.width, bmp.height, bmp.n_channels, bytes(bmp.buffer), bmp.stride)


def pdf_to_perception(data: bytes, *, want_images: bool, max_pages: int = _MAX_PDF_PAGES, max_rendered: int = _MAX_RENDERED_PAGES) -> dict[str, Any]:
    """Turn PDF bytes into a perception dict.

    Returns ``{"text", "images", "pages", "rendered", "scanned"}``:
      - ``text``     concatenated extracted text across the first ``max_pages`` pages
      - ``images``   data-URL PNGs of *scanned* pages (only when ``want_images``), capped
      - ``pages``    total page count in the document
      - ``rendered`` how many pages we rasterized
      - ``scanned``  how many pages had no extractable text (whether or not we rendered them)
    """
    import pypdfium2 as pdfium  # lazy: only a PDF read pays the import

    doc = pdfium.PdfDocument(data)
    total = len(doc)
    parts: list[str] = []
    images: list[str] = []
    scanned = 0
    try:
        for i in range(min(total, max_pages)):
            page = doc[i]
            tp = page.get_textpage()
            text = (tp.get_text_range() or "").strip()
            if len(text.replace(" ", "").replace("\n", "")) < _SCANNED_TEXT_FLOOR:
                scanned += 1
                if want_images and len(images) < max_rendered:
                    images.append("data:image/png;base64," + base64.b64encode(_render_page_png(page)).decode("ascii"))
                if text:
                    parts.append(f"[page {i + 1}]\n{text}")
            else:
                parts.append(f"[page {i + 1}]\n{text}")
    finally:
        doc.close()
    return {"text": "\n\n".join(parts), "images": images, "pages": total, "rendered": len(images), "scanned": scanned}


def to_perception(name: str, data: bytes, *, want_images: bool) -> dict[str, Any]:
    """Dispatch a visual file's bytes to a perception. ``want_images`` is the caller's model
    capability: a vision model passes ``True`` (it gets image blocks); a text-only model passes
    ``False`` (it gets text where there is any, and an honest note where there is not).

    Result shape: ``{"kind", "text", "images", "note", ...}``. ``images`` is a list of data-URL
    strings (empty for text-only callers); ``note`` is a short human line for the scene/the mind.
    """
    kind = kind_of(name, data)
    if kind == "image":
        if want_images:
            return {"kind": "image", "text": "", "images": [image_data_url(name, data)], "note": f"the image {name}"}
        return {"kind": "image", "text": "", "images": [], "note": f"{name} is an image, which this mind cannot see"}
    if kind == "pdf":
        p = pdf_to_perception(data, want_images=want_images)
        bits = [f"a PDF, {p['pages']} page(s)"]
        if p["scanned"]:
            bits.append(f"{p['scanned']} scanned" + (f", {p['rendered']} shown as images" if p["rendered"] else (", which this mind cannot see" if not want_images else "")))
        note = f"{name}: " + "; ".join(bits)
        return {"kind": "pdf", "text": p["text"], "images": p["images"], "note": note, "pages": p["pages"], "scanned": p["scanned"], "rendered": p["rendered"]}
    return {"kind": None, "text": "", "images": [], "note": f"{name} is not a readable image or PDF"}
