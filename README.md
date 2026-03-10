# markup

Convert between Markdown, HTML, and plain text.

One file. Zero deps. Converts text.

## Usage

```bash
python3 markup.py md2html README.md
python3 markup.py html2text page.html
python3 markup.py md2text README.md
echo "# Hello **world**" | python3 markup.py md2html
python3 markup.py md2html README.md --wrap -o output.html
```

## Requirements

Python 3.8+. No dependencies.

## License

MIT
