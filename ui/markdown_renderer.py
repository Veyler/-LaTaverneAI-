"""
Rendu Markdown riche dans un widget tk.Text.
Supporte : titres, gras, italique, code inline/bloc, listes, citations,
séparateurs, <br> + animation de frappe.
"""

import re
import tkinter as tk
import tkinter.font as tkfont
from core import config as cfg


# ─── Segment Collector ───────────────────────────────────────────────────────

class _SegmentCollector:
    """Mimics tk.Text API but collects (text, tags) tuples."""
    def __init__(self):
        self.segments = []

    def insert(self, pos, text, tags=()):
        if isinstance(tags, str):
            tags = (tags,)
        self.segments.append((text, tags))

    def configure(self, **kw): pass
    def delete(self, *a): pass
    def index(self, *a): return "1.0"
    def get(self, *a): return ""


# ─── Widget creation ─────────────────────────────────────────────────────────

def create_markdown_text_widget(parent, bg_color=None):
    if bg_color is None:
        bg_color = cfg.COLORS["ai_bubble"]

    w = tk.Text(
        parent, wrap="word", font=cfg.FONTS["body"],
        bg=bg_color, fg=cfg.COLORS["text_primary"],
        relief="flat", borderwidth=0, highlightthickness=0,
        padx=14, pady=10, cursor="arrow",
        width=1, height=1, state="disabled",
        selectbackground=cfg.COLORS["accent_dim"],
        selectforeground="#0A0E1A", insertwidth=0,
    )
    _configure_tags(w)
    return w


def _configure_tags(widget):
    C = cfg.COLORS
    bf, bs = cfg.FONTS["body"][0], cfg.FONTS["body"][1]
    mf, ms = cfg.FONTS["code"][0], cfg.FONTS["code"][1]

    widget.tag_configure("h1", font=(bf, bs+6, "bold"), foreground=C["h1"], spacing1=10, spacing3=6)
    widget.tag_configure("h2", font=(bf, bs+3, "bold"), foreground=C["h2"], spacing1=8, spacing3=4)
    widget.tag_configure("h3", font=(bf, bs+1, "bold"), foreground=C["h3"], spacing1=6, spacing3=3)
    widget.tag_configure("bold", font=(bf, bs, "bold"), foreground=C["bold_text"])
    widget.tag_configure("italic", font=(bf, bs, "italic"), foreground=C["italic_text"])
    widget.tag_configure("bold_italic", font=(bf, bs, "bold italic"), foreground=C["bold_text"])
    widget.tag_configure("code_inline", font=(mf, ms), foreground=C["inline_code_fg"], background=C["inline_code_bg"])
    widget.tag_configure("code_block", font=(mf, ms), foreground="#C9D1D9", background=C["code_bg"],
                         spacing1=2, spacing3=2, lmargin1=12, lmargin2=12, rmargin=12)
    widget.tag_configure("code_block_header", font=(mf, ms-1), foreground=C["text_dim"], background="#161B22",
                         spacing1=6, spacing3=2, lmargin1=12, lmargin2=12, rmargin=12)
    widget.tag_configure("quote", font=(bf, bs, "italic"), foreground=C["quote_text"], background=C["quote_bg"],
                         lmargin1=20, lmargin2=20, spacing1=2, spacing3=2)
    widget.tag_configure("list_bullet", foreground=C["list_bullet"])
    widget.tag_configure("list_text", lmargin1=24, lmargin2=24)
    widget.tag_configure("list_text_l2", lmargin1=44, lmargin2=44)
    widget.tag_configure("separator", foreground=C["separator"], font=(bf, 4), spacing1=6, spacing3=6, justify="center")
    widget.tag_configure("normal", font=(bf, bs), foreground=C["text_primary"], spacing1=1, spacing3=1)
    widget.tag_configure("paragraph_space", font=(bf, 4))


# ─── Core parser ─────────────────────────────────────────────────────────────

def _parse_markdown(w, content: str):
    content = content.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    lines = content.split("\n")
    i = 0
    first = True

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if not first: w.insert("end", "\n", "paragraph_space")
            lang = line.strip()[3:].strip()
            if lang: w.insert("end", f"  {lang}\n", "code_block_header")
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            w.insert("end", "\n".join(code) + "\n", "code_block")
            i += 1; first = False; continue

        m = re.match(r'^(#{1,3})\s+(.*)', line)
        if m:
            if not first: w.insert("end", "\n", "paragraph_space")
            w.insert("end", _strip_inline(m.group(2)) + "\n", f"h{len(m.group(1))}")
            i += 1; first = False; continue

        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            w.insert("end", "─" * 50 + "\n", "separator")
            i += 1; first = False; continue

        m = re.match(r'^>\s*(.*)', line)
        if m:
            if not first: w.insert("end", "\n", "paragraph_space")
            ql = []
            while i < len(lines):
                qm = re.match(r'^>\s*(.*)', lines[i])
                if qm: ql.append(qm.group(1)); i += 1
                else: break
            w.insert("end", "│ " + " ".join(ql) + "\n", "quote")
            first = False; continue

        m = re.match(r'^(\s*)([-*+]|\d+[.)]) \s*(.*)', line)
        if m:
            indent = len(m.group(1)) // 2
            tag = "list_text_l2" if indent >= 1 else "list_text"
            bullet = m.group(2)
            marker = f"{bullet} " if re.match(r'\d+[.)]', bullet) else "  •  "
            w.insert("end", marker, ("list_bullet", tag))
            _fmt(w, m.group(3), [tag])
            w.insert("end", "\n")
            i += 1; first = False; continue

        if line.strip() == "":
            w.insert("end", "\n", "paragraph_space")
            i += 1; continue

        _fmt(w, line, ["normal"])
        w.insert("end", "\n")
        i += 1; first = False


def _fmt(w, text, base):
    """Parse inline formatting (bold, italic, code) and insert."""
    pat = re.compile(r'(`[^`]+?`)|(\*\*\*(.+?)\*\*\*)|(\*\*(.+?)\*\*)|(\*(.+?)\*)|(__(.+?)__)|(_(.+?)_)')
    last = 0
    for m in pat.finditer(text):
        if m.start() > last:
            w.insert("end", text[last:m.start()], tuple(base))
        if m.group(1):
            w.insert("end", m.group(1)[1:-1], tuple(base + ["code_inline"]))
        elif m.group(2):
            w.insert("end", m.group(3), tuple(base + ["bold_italic"]))
        elif m.group(4):
            w.insert("end", m.group(5), tuple(base + ["bold"]))
        elif m.group(6):
            w.insert("end", m.group(7), tuple(base + ["italic"]))
        elif m.group(8):
            w.insert("end", m.group(9), tuple(base + ["bold"]))
        elif m.group(10):
            w.insert("end", m.group(11), tuple(base + ["italic"]))
        last = m.end()
    if last < len(text):
        w.insert("end", text[last:], tuple(base))


def _strip_inline(t):
    for p, r in [(r'`(.+?)`', r'\1'), (r'\*\*\*(.+?)\*\*\*', r'\1'),
                 (r'\*\*(.+?)\*\*', r'\1'), (r'\*(.+?)\*', r'\1'),
                 (r'__(.+?)__', r'\1'), (r'_(.+?)_', r'\1')]:
        t = re.sub(p, r, t)
    return t


# ─── Render (immediate) ──────────────────────────────────────────────────────

def render_markdown_to_widget(widget, content: str):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    _parse_markdown(widget, content)
    widget.configure(state="disabled")


# ─── Render (animated) ───────────────────────────────────────────────────────

def animate_markdown_to_widget(widget, content, root, on_step=None,
                                on_complete=None, chunk_size=3, delay_ms=8):
    """Typing animation: parse markdown into segments, then insert chunk by chunk."""
    collector = _SegmentCollector()
    _parse_markdown(collector, content)

    # Flatten to character chunks
    ops = []
    for text, tags in collector.segments:
        for i in range(0, max(1, len(text)), chunk_size):
            ops.append((text[i:i + chunk_size], tags))

    widget.configure(state="normal")
    widget.delete("1.0", "end")

    idx = [0]
    step_count = [0]

    def step():
        if idx[0] >= len(ops):
            widget.configure(state="disabled")
            if on_complete:
                on_complete()
            return

        widget.configure(state="normal")
        chunk, tags = ops[idx[0]]
        widget.insert("end", chunk, tags)
        idx[0] += 1
        step_count[0] += 1

        # Auto-resize periodically
        if on_step and step_count[0] % 15 == 0:
            widget.configure(state="disabled")
            on_step()

        root.after(delay_ms, step)

    step()


# ─── Auto-resize ─────────────────────────────────────────────────────────────

def auto_resize_text_widget(widget):
    widget.update_idletasks()
    try:
        dl = widget.count("1.0", "end", "displaylines")
        n = dl[0] if dl and dl[0] else int(widget.index("end-1c").split(".")[0])
    except Exception:
        n = int(widget.index("end-1c").split(".")[0])
    widget.configure(height=n)


# ─── Legacy ──────────────────────────────────────────────────────────────────

def render_markdown_to_text(text: str) -> str:
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r'```[\s\S]*?```', lambda m: m.group(0).strip('`').strip(), text)
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    for p, r in [(r'\*\*\*(.+?)\*\*\*', r'\1'), (r'\*\*(.+?)\*\*', r'\1'),
                 (r'\*(.+?)\*', r'\1'), (r'`(.+?)`', r'\1')]:
        text = re.sub(p, r, text)
    return text