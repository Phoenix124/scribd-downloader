"""
Walks the Everand reader and captures the HTML of every page column.

The reader shows two columns (a spread) at a time and animates page turns,
so every read waits for the DOM to settle first. It must run in a visible,
logged-in real Chrome window to get past Cloudflare.
"""

import base64
import hashlib
import re
import time

NEXT_BUTTON = "button.page_right.next_btn"
PREV_BUTTON = "button.page_left.prev_btn"

# Snapshots both columns, the page counter and the navigation buttons at once
_JS_READER_STATE = r"""
() => {
  const readColumn = (side) => {
    const column = document.querySelector('div.reader_column.' + side);
    if (!column) return { ready: false };
    const content = column.querySelector('[data-content-column]');
    const line = column.querySelector('span.text_line');
    const img = column.querySelector('img');
    const style = content ? (content.getAttribute('style') || '') : '';
    const width = style.match(/width:\s*([0-9.]+)px/);
    const height = style.match(/height:\s*([0-9.]+)px/);
    return {
      ready: !!content && (!!line || !!img) && content.innerHTML.length > 200,
      first: line ? line.getAttribute('data-position')
                  : (img ? 'img:' + (img.getAttribute('src') || '').slice(-48) : null),
      html: content ? content.outerHTML : null,
      w: width ? Math.round(parseFloat(width[1])) : null,
      h: height ? Math.round(parseFloat(height[1])) : null,
    };
  };
  const counter = document.querySelector('div.page_counter');
  const next = document.querySelector('button.page_right.next_btn');
  const prev = document.querySelector('button.page_left.prev_btn');
  return {
    left: readColumn('left_column'),
    right: readColumn('right_column'),
    counter: counter ? counter.innerText.trim() : '',
    nextDisabled: next ? next.disabled : true,
    prevDisabled: prev ? prev.disabled : true,
  };
}
"""

# Clicking through JS so an overlapping cookie banner can't swallow the click
_JS_CLICK = r"""
(selector) => {
  const button = document.querySelector(selector);
  if (!button) return false;
  button.click();
  return true;
}
"""

# Fetches a URL from the reader page itself (same origin, with cookies)
_JS_FETCH_DATA_URI = r"""
async (url) => {
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const blob = await response.blob();
    return await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(blob);
    });
  } catch (e) { return null; }
}
"""


def parse_counter(text):
    """
    Parses the reader's page counter, e.g. 'PAGE 103 OF 243' -> (103, 243).
    Returns (None, None) when it can't be parsed.
    """
    match = re.search(r"(\d+)\s+OF\s+(\d+)", text or "", re.IGNORECASE)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def inline_fonts(context, css):
    """
    Embeds the fonts referenced by `css` as data URIs.

    Pages are rendered later from a blank origin where the font URLs fail
    (CORS, expiring tokens), and fallback fonts make the text overlap.
    """
    for url in set(re.findall(r"url\('([^']+)'\)", css)):
        try:
            response = context.request.get(url, headers={"Referer": "https://www.everand.com/"})
        except Exception as e:
            print("Could not download font: {}".format(e))
            continue
        if not response.ok:
            print("Could not download font: HTTP {}".format(response.status))
            continue
        data = base64.b64encode(response.body()).decode("ascii")
        css = css.replace("url('{}')".format(url), "url('data:font/ttf;base64,{}')".format(data))
    return css


def _inline_images(page, html, cache):
    """
    Embeds the images of a page column as data URIs while their
    tokenized URLs are still valid.
    """
    for src in set(re.findall(r'<img[^>]+src="([^"]+)"', html)):
        if src.startswith("data:"):
            continue
        if src not in cache:
            url = src if src.startswith("http") else "https://www.everand.com" + src
            try:
                cache[src] = page.evaluate(_JS_FETCH_DATA_URI, url)
            except Exception:
                cache[src] = None
            if not cache[src]:
                print("Could not download image: {}".format(src[:60]))
        if cache[src]:
            html = html.replace('src="{}"'.format(src), 'src="{}"'.format(cache[src]))
    return html


def _state(page):
    return page.evaluate(_JS_READER_STATE)


def _click(page, selector):
    return page.evaluate(_JS_CLICK, selector)


def _wait_settled(page, timeout=15.0):
    """
    Waits until the reader has finished turning the page: the columns are
    rendered and two consecutive reads agree. Returns the settled state.
    """
    started = time.time()
    previous_key = None
    state = _state(page)
    while time.time() - started < timeout:
        state = _state(page)
        page_number, _ = parse_counter(state["counter"])
        left_ready = state["left"]["ready"] and page_number is not None
        right_ready = state["right"]["ready"] or state["nextDisabled"]
        key = (state["left"].get("first"), state["right"].get("first"), page_number)
        if left_ready and right_ready and key == previous_key:
            return state
        previous_key = key if left_ready else None
        page.wait_for_timeout(350)
    return state


def _rewind(page):
    """
    Goes back to the first page. Some books never disable the Previous
    button, so also stop once the page counter stops decreasing.
    """
    last_page = None
    stuck = 0
    for _ in range(400):
        state = _wait_settled(page, timeout=8)
        current_page, _ = parse_counter(state["counter"])
        if state["prevDisabled"]:
            break
        if last_page is not None and current_page is not None and current_page >= last_page:
            stuck += 1
            if stuck >= 2:
                break
        else:
            stuck = 0
        last_page = current_page
        if not _click(page, PREV_BUTTON):
            break
        started = time.time()
        while time.time() - started < 5:
            page.wait_for_timeout(250)
            now, _ = parse_counter(_state(page)["counter"])
            if now is not None and current_page is not None and now < current_page:
                break


def capture_book(page, max_pages=0):
    """
    Captures the book front to back, one spread at a time.

    A column can hold several print pages and the page counter isn't unique
    per column, so columns are deduplicated by content hash.

    Returns a list of {"html", "w", "h"} dicts in reading order.
    """
    _rewind(page)
    columns = []
    seen = set()
    image_cache = {}
    idle_turns = 0

    for _ in range(3000):
        state = _wait_settled(page)
        page_number, total = parse_counter(state["counter"])
        added = 0
        for side in ("left", "right"):
            column = state[side]
            if not (column["ready"] and column["html"]):
                continue
            digest = hashlib.md5(column["html"].encode("utf-8", "ignore")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            html = _inline_images(page, column["html"], image_cache)
            columns.append({"html": html, "w": column["w"], "h": column["h"]})
            added += 1
        print("Captured page {} of {} ({} columns)".format(page_number, total, len(columns)))

        if max_pages and len(columns) >= max_pages:
            break
        if state["nextDisabled"]:
            break

        first_line = state["left"].get("first")
        if not _click(page, NEXT_BUTTON):
            idle_turns += 1
            if idle_turns >= 3:
                break
            page.wait_for_timeout(500)
            continue

        turned = False
        started = time.time()
        while time.time() - started < 12:
            page.wait_for_timeout(300)
            new_state = _state(page)
            if new_state["nextDisabled"] or (
                    new_state["left"]["ready"] and new_state["left"].get("first") != first_line):
                turned = True
                break

        idle_turns = 0 if (turned and added) else idle_turns + 1
        if idle_turns >= 3:
            break

    return columns
