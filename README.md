# Fringe Metrology Website

This repository contains the source code for the Fringe Metrology website.

## Project Structure

- `*.html`: Main site pages.
- `blog/`: Blog content, including posts in `blog/posts/` and the blog template.
- `css/`: Stylesheets.
- `js/`: JavaScript files.
- `imgs/`: Images.
- `fonts/`: Font files.

## Development Utilities

The project includes Python scripts to assist with site maintenance.

### Building the Blog

The blog is statically generated from Markdown files. To process new posts and update `blog.html`:

1. Add your `.md` post files to `blog/posts/`.
2. Run the build script:

```bash
python build_blog.py
```

This will convert the Markdown files to HTML and update the blog index.

### Updating Placeholders & Headers/Footers

The `update_placeholders.py` script is used to standardize headers, footers, and handle image placeholders across all HTML files.

To run it:

```bash
python update_placeholders.py
```

To preview changes without applying them:

```bash
python update_placeholders.py --dry-run
```
