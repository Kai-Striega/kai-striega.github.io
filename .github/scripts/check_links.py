"""Check that every internal link in a built Hugo site resolves to a file.

Usage: python3 .github/scripts/check_links.py public

Walks every .html file under the given directory and checks each href/src
that points inside the site: root-relative (/blog/...) or relative
(../images/x.svg). External URLs, mailto:, data: and same-page #fragments are
skipped; absolute links to the site's own domain come from .Permalink and are
not checked. A link to a directory counts as resolved when the directory has
an index.html. Exits non-zero, listing each broken link, if any are found.

Standard library only, so CI needs nothing installed beyond Python.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK_ATTRS = {"href", "src"}
SKIP_SCHEMES = ("http:", "https:", "mailto:", "tel:", "data:", "javascript:")


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    # Every tag counts; `tag` is unused but its name is fixed by HTMLParser.
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in LINK_ATTRS and value:
                self.links.append(value.strip())


def is_internal(link):
    return not (
        link.startswith("#")
        or link.startswith("//")
        or link.lower().startswith(SKIP_SCHEMES)
    )


def resolves(root, page, link):
    path = unquote(urlsplit(link).path)
    if not path:  # "?query" or "#frag" only: refers to the page itself
        return True
    target = root / path.lstrip("/") if path.startswith("/") else page.parent / path
    return target.is_file() or (target / "index.html").is_file()


def main(argv):
    if len(argv) != 2:
        print("usage: check_links.py <built-site-dir>", file=sys.stderr)
        return 2
    root = Path(argv[1]).resolve()
    pages = sorted(root.rglob("*.html"))
    if not pages:
        print(f"No HTML files under {root}; was the site built?", file=sys.stderr)
        return 2

    broken = []
    checked = 0
    for page in pages:
        collector = LinkCollector()
        collector.feed(page.read_text(encoding="utf-8"))
        for link in filter(is_internal, collector.links):
            checked += 1
            if not resolves(root, page, link):
                broken.append((page.relative_to(root), link))

    for page, link in broken:
        print(f"{page}: broken link {link}")
    print(f"Checked {checked} internal links across {len(pages)} pages: "
          f"{len(broken)} broken.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
