#!/usr/bin/env python3
"""markup - Convert between Markdown, HTML, and plain text.

One file. Zero deps. Converts text.

Usage:
  markup.py md2html README.md             → Markdown to HTML
  markup.py html2text page.html           → HTML to plain text
  markup.py html2md page.html             → HTML to Markdown (basic)
  markup.py md2text README.md             → Markdown to plain text
  echo "# Hello" | markup.py md2html     → pipe input
"""

import argparse
import html
import re
import sys


def md_to_html(text: str) -> str:
    """Convert Markdown to HTML (subset)."""
    lines = text.split('\n')
    result = []
    in_code = False
    in_list = False
    in_para = False

    for line in lines:
        # Fenced code blocks
        if line.strip().startswith('```'):
            if in_code:
                result.append('</code></pre>')
                in_code = False
            else:
                lang = line.strip()[3:].strip()
                cls = f' class="language-{lang}"' if lang else ''
                result.append(f'<pre><code{cls}>')
                in_code = True
            continue
        if in_code:
            result.append(html.escape(line))
            continue

        stripped = line.strip()

        # Close list if needed
        if in_list and not stripped.startswith(('- ', '* ', '+ ')) and not re.match(r'^\d+\.', stripped):
            result.append('</ul>')
            in_list = False

        # Headings
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            if in_para:
                result.append('</p>')
                in_para = False
            level = len(m.group(1))
            content = inline_md(m.group(2))
            result.append(f'<h{level}>{content}</h{level}>')
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            result.append('<hr>')
            continue

        # Unordered list
        if re.match(r'^[-*+]\s+', stripped):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = inline_md(re.sub(r'^[-*+]\s+', '', stripped))
            result.append(f'<li>{content}</li>')
            continue

        # Ordered list
        m = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if m:
            if not in_list:
                result.append('<ol>')
                in_list = True
            result.append(f'<li>{inline_md(m.group(2))}</li>')
            continue

        # Blockquote
        if stripped.startswith('>'):
            content = inline_md(stripped.lstrip('> '))
            result.append(f'<blockquote>{content}</blockquote>')
            continue

        # Empty line
        if not stripped:
            if in_para:
                result.append('</p>')
                in_para = False
            continue

        # Paragraph
        if not in_para:
            result.append('<p>')
            in_para = True
        result.append(inline_md(stripped))

    if in_para:
        result.append('</p>')
    if in_list:
        result.append('</ul>')
    if in_code:
        result.append('</code></pre>')

    return '\n'.join(result)


def inline_md(text: str) -> str:
    """Process inline Markdown."""
    # Code spans
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold + italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    # Strikethrough
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Images
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    return text


def html_to_text(text: str) -> str:
    """Strip HTML to plain text."""
    # Remove scripts and styles
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Block elements → newlines
    text = re.sub(r'<(br|hr|/p|/div|/h[1-6]|/li|/tr)[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>', '• ', text, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode entities
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def md_to_text(text: str) -> str:
    """Markdown to plain text."""
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Links → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Headings → text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Bold/italic
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.+?)_{1,3}', r'\1', text)
    # Strikethrough
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Code blocks
    text = re.sub(r'```[^\n]*\n(.*?)```', r'\1', text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # List markers
    text = re.sub(r'^[-*+]\s+', '• ', text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    return text.strip()


def main():
    parser = argparse.ArgumentParser(description="Convert between text formats")
    parser.add_argument("command", choices=["md2html", "html2text", "md2text", "html2md"])
    parser.add_argument("file", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--wrap", action="store_true", help="Wrap HTML in full document")

    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("Error: no input", file=sys.stderr)
        return 1

    converters = {
        "md2html": md_to_html,
        "html2text": html_to_text,
        "md2text": md_to_text,
        "html2md": html_to_text,  # basic: just strip tags
    }

    result = converters[args.command](text)

    if args.command == "md2html" and args.wrap:
        result = f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'></head>\n<body>\n{result}\n</body></html>"

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
