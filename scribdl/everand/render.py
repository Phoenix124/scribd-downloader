"""
Renders captured Everand page columns into a single PDF with selectable text.

Rendering happens in headless Chromium because Playwright can only print
PDFs there. Captured columns carry the reader's uneven on-screen margins,
so each page is re-cropped to its content: text pages share one size (the
largest text block in the book), image-only pages (cover, dividers) get
their own tight size.
"""

import math
import os

# Blank space in px around the content of every page
MARGIN = 48

_BASE_CSS = ("@page{margin:0}*{box-sizing:border-box}"
             "html,body{margin:0;padding:0;background:#fff}"
             "[data-content-column]{transform:none !important}")

# Measures the content box. Text is measured through a Range because text
# lines are width:100% boxes that would inflate the width.
_JS_MEASURE = r"""
() => {
  const range = document.createRange();
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, found = false, hasText = false;
  const add = (r) => {
    if (r.width > 0 && r.height > 0) {
      found = true;
      x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top);
      x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom);
    }
  };
  for (const el of document.querySelectorAll('span.text_line')) {
    range.selectNodeContents(el);
    const r = range.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) hasText = true;
    add(r);
  }
  for (const el of document.querySelectorAll('[data-content-column] img')) {
    add(el.getBoundingClientRect());
  }
  return found ? {x0, y0, x1, y1, hasText} : null;
}
"""

# Moves the column into a clipping frame of the page size, top-aligned and
# optionally centred horizontally
_JS_PLACE = r"""
(a) => {
  const column = document.querySelector('[data-content-column]');
  const frame = document.createElement('div');
  frame.style.cssText = `position:relative;width:${a.W}px;height:${a.H}px;overflow:hidden;background:#fff;`;
  document.body.insertBefore(frame, document.body.firstChild);
  frame.appendChild(column);
  column.style.position = 'absolute';
  const left = a.center ? (a.W - (a.x1 - a.x0)) / 2 : a.M;
  column.style.left = (left - a.x0) + 'px';
  column.style.top = (a.M - a.y0) + 'px';
  const size = `margin:0;padding:0;width:${a.W}px;height:${a.H}px;overflow:hidden;`;
  document.documentElement.style.cssText = size;
  document.body.style.cssText = size;
}
"""

_JS_WAIT_RESOURCES = r"""
async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
}
"""


def _load(page, column, fontfaces):
    html = (column["html"] or "").replace('src="/', 'src="https://www.everand.com/')
    document = ("<!doctype html><html><head><meta charset='utf-8'>"
                "<style>{}{}</style></head><body>{}</body></html>").format(_BASE_CSS, fontfaces, html)
    try:
        page.set_content(document, wait_until="networkidle", timeout=20000)
    except Exception:
        page.set_content(document, wait_until="load", timeout=20000)
    try:
        page.evaluate(_JS_WAIT_RESOURCES)
    except Exception:
        pass


def _box_size(box):
    return (math.ceil(box["x1"] - box["x0"] + 2 * MARGIN),
            math.ceil(box["y1"] - box["y0"] + 2 * MARGIN))


def render_pages(browser, columns, fontfaces, directory):
    """
    Renders every column to its own PDF inside `directory`.
    Returns the list of written paths in reading order.
    """
    page = browser.new_page()

    # First pass measures every page to find the shared text page size
    boxes = []
    for column in columns:
        _load(page, column, fontfaces)
        boxes.append(page.evaluate(_JS_MEASURE))
    text_sizes = [_box_size(box) for box in boxes if box and box["hasText"]]
    text_size = (max(w for w, _ in text_sizes), max(h for _, h in text_sizes)) if text_sizes else None

    paths = []
    for number, (column, box) in enumerate(zip(columns, boxes), 1):
        _load(page, column, fontfaces)
        if box and box["hasText"]:
            width, height = text_size
            page.evaluate(_JS_PLACE, dict(box, W=width, H=height, M=MARGIN, center=True))
        elif box:
            width, height = _box_size(box)
            page.evaluate(_JS_PLACE, dict(box, W=width, H=height, M=MARGIN, center=False))
        else:
            width, height = column["w"] or 1015, column["h"] or 1544

        path = os.path.join(directory, "{:05d}.pdf".format(number))
        page.pdf(path=path, width="{}px".format(width), height="{}px".format(height), print_background=True)
        paths.append(path)
        print("Rendered page {} of {}".format(number, len(columns)))

    page.close()
    return paths


def merge_pdfs(paths, output_path):
    """
    Joins single-page PDFs into one file.
    """
    from pypdf import PdfWriter

    writer = PdfWriter()
    for path in paths:
        writer.append(path)
    with open(output_path, "wb") as f:
        writer.write(f)
