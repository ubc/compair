# -*- coding: utf-8 -*-
import unittest

from compair.sanitization import sanitize_html


class SanitizeHtmlTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_none_returns_none(self):
        assert sanitize_html(None) is None

    def test_empty_string_returns_empty(self):
        assert sanitize_html("") == ""

    # ------------------------------------------------------------------
    # Allowed tags pass through
    # ------------------------------------------------------------------

    def test_allowed_block_tags(self):
        for tag in ["p", "h1", "h2", "h3", "pre", "blockquote"]:
            result = sanitize_html(f"<{tag}>text</{tag}>")
            assert f"<{tag}>" in result, f"<{tag}> should be preserved"

    def test_allowed_inline_tags(self):
        for tag in ["strong", "em", "u", "s", "del", "code", "span",
                    "big", "small", "tt", "kbd", "samp", "var",
                    "ins", "cite", "q"]:
            result = sanitize_html(f"<{tag}>text</{tag}>")
            assert f"<{tag}>" in result, f"<{tag}> should be preserved"

    def test_br_preserved(self):
        assert "<br>" in sanitize_html("<p>line1<br />line2</p>")

    def test_allowed_list_tags(self):
        html = "<ul><li>item</li></ul>"
        result = sanitize_html(html)
        assert "<ul>" in result
        assert "<li>" in result

    def test_allowed_table_tags(self):
        html = "<table><thead><tr><th>h</th></tr></thead><tbody><tr><td>d</td></tr></tbody></table>"
        result = sanitize_html(html)
        for tag in ["table", "thead", "tbody", "tr", "th", "td"]:
            assert f"<{tag}" in result, f"<{tag}> should be preserved"

    def test_link_preserved(self):
        result = sanitize_html('<a href="https://example.com">link</a>')
        assert 'href="https://example.com"' in result

    def test_image_preserved(self):
        result = sanitize_html('<img src="https://example.com/img.png" alt="test">')
        assert 'src="https://example.com/img.png"' in result
        assert 'alt="test"' in result

    # ------------------------------------------------------------------
    # Disallowed tags stripped
    # ------------------------------------------------------------------

    def test_script_tag_and_content_removed(self):
        result = sanitize_html("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "alert(1)" not in result

    def test_style_tag_and_content_removed(self):
        result = sanitize_html("<style>body{color:red}</style>")
        assert "<style>" not in result
        assert "color:red" not in result

    def test_iframe_stripped(self):
        result = sanitize_html('<iframe src="https://evil.com"></iframe>')
        assert "<iframe" not in result

    def test_unknown_tag_stripped(self):
        result = sanitize_html("<marquee>text</marquee>")
        assert "<marquee>" not in result
        assert "text" in result

    # ------------------------------------------------------------------
    # Event handler attributes stripped
    # ------------------------------------------------------------------

    def test_onclick_stripped(self):
        result = sanitize_html('<p onclick="alert(1)">text</p>')
        assert "onclick" not in result

    def test_onerror_stripped(self):
        result = sanitize_html('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result

    # ------------------------------------------------------------------
    # URL scheme filtering
    # ------------------------------------------------------------------

    def test_javascript_href_stripped(self):
        result = sanitize_html('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in result

    def test_http_href_allowed(self):
        result = sanitize_html('<a href="http://example.com">link</a>')
        assert 'href="http://example.com"' in result

    def test_https_href_allowed(self):
        result = sanitize_html('<a href="https://example.com">link</a>')
        assert 'href="https://example.com"' in result

    def test_mailto_href_allowed(self):
        result = sanitize_html('<a href="mailto:foo@bar.com">email</a>')
        assert 'href="mailto:foo@bar.com"' in result

    def test_data_uri_src_stripped(self):
        result = sanitize_html('<img src="data:image/png;base64,abc">')
        assert "data:" not in result

    # ------------------------------------------------------------------
    # rel="noopener noreferrer" injected automatically
    # ------------------------------------------------------------------

    def test_noopener_injected_on_blank_target(self):
        result = sanitize_html('<a href="https://example.com" target="_blank">link</a>')
        assert "noopener" in result
        assert "noreferrer" in result

    def test_user_supplied_rel_overridden(self):
        result = sanitize_html('<a href="https://example.com" target="_blank" rel="opener">link</a>')
        assert "opener" not in result or "noopener" in result

    # ------------------------------------------------------------------
    # Class filtering
    # ------------------------------------------------------------------

    def test_combinedmath_class_preserved(self):
        result = sanitize_html('<span class="combinedmath">math</span>')
        assert 'class="combinedmath"' in result

    def test_marker_class_preserved(self):
        result = sanitize_html('<span class="marker">text</span>')
        assert 'class="marker"' in result

    def test_unknown_class_stripped(self):
        result = sanitize_html('<span class="evil-class">text</span>')
        assert "evil-class" not in result

    def test_language_class_on_code_preserved(self):
        for lang in ["language-python", "language-javascript", "language-bash"]:
            result = sanitize_html(f'<pre><code class="{lang}">code</code></pre>')
            assert lang in result, f"{lang} should be preserved"

    def test_unknown_language_class_stripped(self):
        result = sanitize_html('<code class="language-evil">code</code>')
        assert "language-evil" not in result

    def test_language_class_not_allowed_on_span(self):
        result = sanitize_html('<span class="language-python">text</span>')
        assert "language-python" not in result

    # ------------------------------------------------------------------
    # CSS property filtering
    # ------------------------------------------------------------------

    def test_allowed_css_properties_preserved(self):
        for prop in ["float:left", "width:100px", "height:100px",
                     "display:inline-block", "margin:5px"]:
            result = sanitize_html(f'<span style="{prop}">text</span>')
            assert prop.split(":")[0] in result, f"{prop} should be preserved"

    def test_disallowed_css_property_stripped(self):
        result = sanitize_html('<span style="position:fixed">text</span>')
        assert "position" not in result

    def test_color_css_stripped(self):
        result = sanitize_html('<span style="color:red">text</span>')
        assert "color" not in result

    # ------------------------------------------------------------------
    # Table attributes
    # ------------------------------------------------------------------

    def test_table_attributes_preserved(self):
        html = '<table border="1" cellpadding="2" cellspacing="2" summary="test">'
        result = sanitize_html(html)
        assert 'border="1"' in result
        assert 'cellpadding="2"' in result
        assert 'summary="test"' in result

    def test_colspan_rowspan_preserved(self):
        html = '<table><tr><td colspan="2">merged</td></tr></table>'
        result = sanitize_html(html)
        assert 'colspan="2"' in result

    def test_th_scope_preserved(self):
        html = '<table><tr><th scope="col">header</th></tr></table>'
        result = sanitize_html(html)
        assert 'scope="col"' in result

    # ------------------------------------------------------------------
    # href attribute_filter — encoded character injection
    # ------------------------------------------------------------------

    def test_quot_in_href_strips_href(self):
        # &quot; bypass: onload hidden inside href value evades $sanitize
        result = sanitize_html(
            '<a href="https://example.com/evil.pdf&quot; onload=&quot;alert(1)&quot;">click</a>'
        )
        assert 'href=' not in result
        assert 'onload' not in result
        assert 'click' in result

    def test_apos_in_href_strips_href(self):
        result = sanitize_html('<a href="https://example.com/&#39;test">click</a>')
        assert 'href=' not in result

    def test_lt_in_href_strips_href(self):
        result = sanitize_html('<a href="https://example.com/&lt;test">click</a>')
        assert 'href=' not in result

    def test_gt_in_href_strips_href(self):
        result = sanitize_html('<a href="https://example.com/&gt;test">click</a>')
        assert 'href=' not in result

    def test_backtick_in_href_strips_href(self):
        result = sanitize_html('<a href="https://example.com/&#96;test">click</a>')
        assert 'href=' not in result

    def test_clean_href_preserved(self):
        result = sanitize_html('<a href="https://example.com/file.pdf">click</a>')
        assert 'href="https://example.com/file.pdf"' in result

    # ------------------------------------------------------------------
    # Angular template injection (stored as literal text)
    # ------------------------------------------------------------------

    def test_angular_template_injection_is_inert(self):
        html = "<p>{{constructor.constructor('alert(1)')()}}</p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<script>" not in result
