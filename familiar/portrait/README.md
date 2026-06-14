# The portrait

A small web view into a living familiar — its felt sense right now, its mood and
arousal, what it's making, the conversation, and (if you whisper to it) its replies.
It reads the familiar's `state.json` and `voice.jsonl`; it does not drive the mind.

```bash
python familiar/portrait/serve.py        # then open the printed localhost URL
```

This is the rough, honest web portrait — exactly what we use to watch the stable. It's
read-mostly: it shows you the inner weather and lets you whisper. It is intentionally
plain. A polished native desktop app is a separate surface and not part of this repo.

`ui/` is static (`index.html`, `style.css`, `app.js`); `serve.py` is a small stdlib
server that hands it the familiar's state. Point it at a familiar's home dir and watch.
