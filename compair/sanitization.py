import re
import nh3

_UNSAFE_HREF_CHARS = re.compile(r'["\'<>`]')


def _attribute_filter(tag, name, value):
    if tag == 'a' and name == 'href':
        if _UNSAFE_HREF_CHARS.search(value):
            return None
    return value


_CLEANER = nh3.Cleaner(
    tags={
        # Block elements
        "p", "h1", "h2", "h3", "pre", "blockquote",
        # Inline formatting
        "span", "strong", "em", "u", "s", "del", "code",
        "big", "small", "tt", "kbd", "samp", "var", "ins", "cite", "q",
        # Line break
        "br",
        # Links and images
        "a", "img",
        # Tables
        "table", "thead", "tbody", "tr", "th", "td", "caption",
        # Lists
        "ul", "ol", "li",
    },
    clean_content_tags={"script", "style"},
    attributes={
        "span": {"style", "dir"},
        "a": {"href", "target"},   # rel is injected via link_rel
        "img": {"src", "alt", "style"},
        "table": {"border", "cellpadding", "cellspacing", "summary", "align", "style"},
        "th": {"scope", "colspan", "rowspan"},
        "td": {"colspan", "rowspan"},
    },
    allowed_classes={
        "span": {"combinedmath", "marker"},
        "code": {
            "language-apache", "language-bash", "language-coffeescript",
            "language-cpp", "language-cs", "language-css", "language-diff",
            "language-html", "language-http", "language-ini", "language-java",
            "language-javascript", "language-json", "language-makefile",
            "language-markdown", "language-nginx", "language-objectivec",
            "language-perl", "language-php", "language-python", "language-ruby",
            "language-sql", "language-vbscript", "language-xhtml", "language-xml",
        },
    },
    # CSS property whitelist from CKEditor's toolbar
    filter_style_properties={
        # image
        "float",
        "border-style",
        "border-width",
        "margin",
        # image and table
        "width",
        "height",
        # spans with class=combinedmath use this for inline-block
        "display",
    },
    # ftp and news are pretty much obsolete but CKEditor allows them
    url_schemes={"http", "https", "mailto", "ftp", "news"},
    attribute_filter=_attribute_filter,
)


def sanitize_html(html: "str | None") -> "str | None":
    """Sanitize CKEditor-produced HTML before storing to the database."""
    if not html:
        return html
    return _CLEANER.clean(html)
