#!/usr/bin/env python3
"""
build.py - Combined build script for Fringe Metrology website.

This script performs two main functions:
1. Builds the blog:
   - Converts Markdown posts from blog/posts/ to HTML files in the root directory.
   - Updates blog.html with the list of posts.
2. Updates placeholders and common elements:
   - Scans HTML files for image-placeholder divs and updates them.
   - Updates headers and footers to standard templates.
   - Updates the partners section in index.html.

Usage:
    python build.py [--dry-run] [--skip-common]
"""

import os
import glob
import markdown
import yaml
import datetime
import re
import sys
from pathlib import Path

# ==========================================
# Configuration
# ==========================================

SCRIPT_DIR = Path(__file__).parent
BLOG_DIR = SCRIPT_DIR / 'blog'
POSTS_DIR = BLOG_DIR / 'posts'
TEMPLATE_FILE = BLOG_DIR / 'template.html'
BLOG_INDEX_FILE = SCRIPT_DIR / 'blog.html'
IMGS_DIR = SCRIPT_DIR / "imgs"

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.avif'}

# ==========================================
# Standard Templates
# ==========================================

# Standard footer HTML (for root-level pages)
STANDARD_FOOTER = """    <footer>
        <p>&copy; 2026 Fringe Metrology. All rights reserved.</p>
        <div class="footer-links">
            <a href="contact.html">Contact Us</a>
            <span class="footer-divider">|</span>
            <a href="terms.html">Terms of Use</a>
            <span class="footer-divider">|</span>
            <a href="privacy.html">Privacy Policy</a>
        </div>
    </footer>"""

# Standard footer HTML (for blog/ pages - uses relative paths)
STANDARD_FOOTER_BLOG = """    <footer>
        <p>&copy; 2026 Fringe Metrology. All rights reserved.</p>
        <div class="footer-links">
            <a href="../contact.html">Contact Us</a>
            <span class="footer-divider">|</span>
            <a href="../terms.html">Terms of Use</a>
            <span class="footer-divider">|</span>
            <a href="../privacy.html">Privacy Policy</a>
        </div>
    </footer>"""

# Standard header HTML (for root-level pages)
STANDARD_HEADER = """    <header class="scrolled">
        <div class="logo-container">
            <a href="index.html" class="logo-link">
                <img src="imgs/color.png" alt="Fringe Metrology Logo" class="logo-img">
                <span class="logo-text">Fringe Metrology</span>
            </a>
        </div>
        <nav>
            <ul>
                <li class="nav-item">
                    <a href="#">Products</a>
                    <div class="dropdown">
                        <div class="dropdown-content">
                            <div class="dropdown-featured">
                                <a href="fringescan.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/fringescan.gif')"></div>
                                    <div class="card-text">
                                        <h4>FringeScan</h4>
                                        <p>High precision, large area surface scanning<svg class="arrow-right"
                                                width="12" height="12" viewBox="0 0 24 24" fill="none"
                                                stroke="currentColor" stroke-width="3" stroke-linecap="round"
                                                stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                                <a href="fringeshot.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/16mm_fringeshot.jpg')">
                                    </div>
                                    <div class="card-text">
                                        <h4>FringeShot</h4>
                                        <p>Rapid Capture Technology <svg class="arrow-right" width="12" height="12"
                                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
                                                stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </li>
                <li class="nav-item">
                    <a href="#">Technology</a>
                    <div class="dropdown">
                        <div class="dropdown-content">
                            <div class="dropdown-featured">
                                <a href="projection.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/fringescan_custom_systems.jpg')"></div>
                                    <div class="card-text">
                                        <h4>Fringe Projection Profilometry</h4>
                                        <p>High precision, large surfaces <svg class="arrow-right" width="12"
                                                height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                                <a href="structured-light.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/chips.png')"></div>
                                    <div class="card-text">
                                        <h4>Structured Light Autocollimator</h4>
                                        <p>Ultra precision, small surface <svg class="arrow-right" width="12"
                                                height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </li>
                <li class="nav-item"><a href="about.html">About Us</a></li>
                <li class="nav-item"><a href="blog.html">Blog</a></li>
                <li class="nav-item"><a href="contact.html">Contact Us</a></li>
            </ul>
        </nav>
        <button class="mobile-nav-toggle" aria-label="Toggle navigation">
            <span class="hamburger-bar"></span>
            <span class="hamburger-bar"></span>
            <span class="hamburger-bar"></span>
        </button>
    </header>"""

# Standard header for index.html (no scrolled class by default)
STANDARD_HEADER_INDEX = """    <header>
        <div class="logo-container">
            <a href="index.html" class="logo-link">
                <img src="imgs/color.png" alt="Fringe Metrology Logo" class="logo-img">
                <span class="logo-text">Fringe Metrology</span>
            </a>
        </div>
        <nav>
            <ul>
                <li class="nav-item">
                    <a href="#">Products</a>
                    <div class="dropdown">
                        <div class="dropdown-content">
                            <div class="dropdown-featured">
                                <a href="fringescan.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/fringescan.gif')"></div>
                                    <div class="card-text">
                                        <h4>FringeScan</h4>
                                        <p>High precision, large area surface scanning<svg class="arrow-right"
                                                width="12" height="12" viewBox="0 0 24 24" fill="none"
                                                stroke="currentColor" stroke-width="3" stroke-linecap="round"
                                                stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                                <a href="fringeshot.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/16mm_fringeshot.jpg')">
                                    </div>
                                    <div class="card-text">
                                        <h4>FringeShot</h4>
                                        <p>Rapid Capture Technology <svg class="arrow-right" width="12" height="12"
                                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
                                                stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </li>
                <li class="nav-item">
                    <a href="#">Technology</a>
                    <div class="dropdown">
                        <div class="dropdown-content">
                            <div class="dropdown-featured">
                                <a href="projection.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/fringescan_custom_systems.jpg')"></div>
                                    <div class="card-text">
                                        <h4>Fringe Projection Profilometry</h4>
                                        <p>High precision, large surfaces <svg class="arrow-right" width="12"
                                                height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                                <a href="structured-light.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('imgs/chips.png')"></div>
                                    <div class="card-text">
                                        <h4>Structured Light Autocollimator</h4>
                                        <p>Ultra precision, small surface <svg class="arrow-right" width="12"
                                                height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </li>
                <li class="nav-item"><a href="about.html">About Us</a></li>
                <li class="nav-item"><a href="blog.html">Blog</a></li>
                <li class="nav-item"><a href="contact.html">Contact Us</a></li>
            </ul>
        </nav>
        <button class="mobile-nav-toggle" aria-label="Toggle navigation">
            <span class="hamburger-bar"></span>
            <span class="hamburger-bar"></span>
            <span class="hamburger-bar"></span>
        </button>
    </header>"""

# Standard header HTML (for blog/ pages - uses relative paths)
STANDARD_HEADER_BLOG = """    <header class="scrolled">
        <div class="logo-container">
            <a href="../index.html" class="logo-link">
                <img src="../imgs/color.png" alt="Fringe Metrology Logo" class="logo-img">
                <span class="logo-text">Fringe Metrology</span>
            </a>
        </div>
        <nav>
            <ul>
                <li class="nav-item">
                    <a href="#">Products</a>
                    <div class="dropdown">
                        <div class="dropdown-content">
                            <div class="dropdown-featured">
                                <a href="../fringescan.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('../imgs/fringescan.gif')"></div>
                                    <div class="card-text">
                                        <h4>FringeScan</h4>
                                        <p>High precision, large area surface scanning<svg class="arrow-right"
                                                width="12" height="12" viewBox="0 0 24 24" fill="none"
                                                stroke="currentColor" stroke-width="3" stroke-linecap="round"
                                                stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                                <a href="../fringeshot.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('../imgs/16mm_fringeshot.jpg')">
                                    </div>
                                    <div class="card-text">
                                        <h4>FringeShot</h4>
                                        <p>Rapid Capture Technology <svg class="arrow-right" width="12" height="12"
                                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
                                                stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </li>
                <li class="nav-item">
                    <a href="#">Technology</a>
                    <div class="dropdown">
                        <div class="dropdown-content">
                            <div class="dropdown-featured">
                                <a href="../projection.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('../imgs/fringescan_custom_systems.jpg')"></div>
                                    <div class="card-text">
                                        <h4>Fringe Projection Profilometry</h4>
                                        <p>High precision, large surfaces <svg class="arrow-right" width="12"
                                                height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                                <a href="../structured-light.html" class="featured-card">
                                    <div class="card-image" style="background-image: url('../imgs/chips.png')"></div>
                                    <div class="card-text">
                                        <h4>Structured Light Autocollimator</h4>
                                        <p>Ultra precision, small surface <svg class="arrow-right" width="12"
                                                height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="7" y1="17" x2="17" y2="7"></line>
                                                <polyline points="7 7 17 7 17 17"></polyline>
                                            </svg></p>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </li>
                <li class="nav-item"><a href="../about.html">About Us</a></li>
                <li class="nav-item"><a href="../blog.html">Blog</a></li>
                <li class="nav-item"><a href="../contact.html">Contact Us</a></li>
            </ul>
        </nav>
        <button class="mobile-nav-toggle" aria-label="Toggle navigation">
            <span class="hamburger-bar"></span>
            <span class="hamburger-bar"></span>
            <span class="hamburger-bar"></span>
        </button>
    </header>"""

# ==========================================
# Blog Building Functions
# ==========================================

def load_template():
    if not TEMPLATE_FILE.exists():
        print(f"Error: Template file not found at {TEMPLATE_FILE}")
        return ""
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def parse_post(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter and content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])
            markdown_content = parts[2]
            return metadata, markdown_content
    
    # Fallback if no frontmatter
    return {}, content

def generate_post_html(metadata, markdown_content, template):
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content)
    
    # Inject into template
    title = metadata.get('title', 'Blog Post')
    image = metadata.get('image', '')
    
    hero_class = ""
    hero_style = ""
    
    if image:
        hero_class = "has-image"
        # image in frontmatter might have ../imgs/foo.png
        # Since the page is now in root, we remove ../
        if image.startswith('../'):
            image = image[3:]
        hero_style = f"background-image: url('{image}');"
    
    # Also fix paths inside markdown content
    html_content = html_content.replace('../imgs/', 'imgs/')
    html_content = html_content.replace('../index.html', 'index.html')
    html_content = html_content.replace('../blog.html', 'blog.html')
    html_content = html_content.replace('../contact.html', 'contact.html')
    html_content = html_content.replace('../about.html', 'about.html')
    
    # Format date
    date_obj = metadata.get('date')
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d')
        except:
            date_obj = datetime.datetime.now()
    elif not date_obj:
        date_obj = datetime.datetime.now()
        
    date_str = date_obj.strftime('%B %d, %Y')
    
    # Simple replacement - in a real app might use Jinja2
    output_html = template.replace('{{ title }}', title)
    output_html = output_html.replace('{{ content }}', html_content)
    output_html = output_html.replace('{{ hero_class }}', hero_class)
    output_html = output_html.replace('{{ hero_style }}', hero_style)
    output_html = output_html.replace('{{ date }}', date_str)
    
    return output_html

def update_blog_index(posts):
    if not BLOG_INDEX_FILE.exists():
        print(f"Error: Blog index file not found at {BLOG_INDEX_FILE}")
        return

    with open(BLOG_INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Sort posts by date desc
    posts.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    marker_start = '<!-- BLOG_POSTS_START -->'
    marker_end = '<!-- BLOG_POSTS_END -->'
    
    if marker_start not in content or marker_end not in content:
        print(f"Error: Markers not found in {BLOG_INDEX_FILE}")
        return

    # Generate HTML for cards
    cards_html = f"{marker_start}\n"
    cards_html += "                    <!-- Posts will be injected here by build_blog.py -->\n"
    
    for post in posts:
        if post.get('hidden') is True:
            continue
        # Format date
        date_obj = post.get('date')
        if isinstance(date_obj, str):
             try:
                date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d')
             except:
                date_obj = datetime.datetime.now() # Fallback
        
        date_str = date_obj.strftime('%B %d, %Y') if date_obj else ""
        image = post.get('image', 'imgs/card3.jpg')
        # Fix image path for blog index (which is in root)
        # Post frontmatter might have ../imgs/foo.png (relative to post file)
        # We need imgs/foo.png (relative to root)
        if image.startswith('../'):
            image = image[3:]
            
        link = f"{post['filename'].replace('.md', '.html')}"
        title = post.get('title', 'Untitled')
        description = post.get('description', '')
        
        cards_html += f'''
                    <article class="blog-card" data-type="{post.get('type', 'Case Study').replace(' ', '-').lower()}">
                        <div class="blog-card-image" style="background-image: url('{image}')"></div>
                        <div class="blog-card-content">
                            <span class="blog-type">{post.get('type', 'Case Study')}</span>
                            <span class="blog-date">{date_str}</span>
                            <h3>{title}</h3>
                            <p>{description}</p>
                            <a href="{link}" class="read-more">Read More <svg class="arrow-right" width="12" height="12"
                                    viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
                                    stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="7" y1="17" x2="17" y2="7"></line>
                                    <polyline points="7 7 17 7 17 17"></polyline>
                                </svg></a>
                        </div>
                    </article>
'''
    cards_html += f"                    {marker_end}"
    
    # Replace content between markers
    start_idx = content.find(marker_start)
    end_idx = content.find(marker_end) + len(marker_end)
    
    new_content = content[:start_idx] + cards_html + content[end_idx:]
    
    with open(BLOG_INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {BLOG_INDEX_FILE}")

def run_build_blog():
    print("\n=== Building Blog ===\n")
    if not POSTS_DIR.exists():
        print(f"No posts directory found at {POSTS_DIR}")
        return

    template = load_template()
    if not template:
        return

    processed_posts = []

    for filename in glob.glob(os.path.join(POSTS_DIR, '*.md')):
        print(f"Processing {filename}...")
        metadata, markdown_content = parse_post(filename)
        
        # Add filename to metadata for linking
        metadata['filename'] = os.path.basename(filename)
        
        # Generate HTML
        html = generate_post_html(metadata, markdown_content, template)
        
        # Save HTML file in root directory
        output_filename = os.path.basename(filename).replace('.md', '.html')
        output_path = SCRIPT_DIR / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Saved {output_path}")
        processed_posts.append(metadata)

    update_blog_index(processed_posts)

# ==========================================
# Placeholder & Common Elements Functions
# ==========================================

def get_available_images():
    """Scan imgs folder and return a dict of basename -> full filename."""
    images = {}
    if not IMGS_DIR.exists():
        print(f"Warning: imgs directory not found at {IMGS_DIR}")
        return images
    
    for img_file in IMGS_DIR.iterdir():
        if img_file.is_file() and img_file.suffix.lower() in IMAGE_EXTENSIONS:
            # Store by stem (name without extension) for flexible matching
            stem = img_file.stem.lower()
            images[stem] = img_file.name
            # Also store the full name for exact matches
            images[img_file.name.lower()] = img_file.name
    
    return images

def find_placeholders(html_content):
    """Find all image-placeholder divs and their content."""
    # Match: <div class="image-placeholder">filename.ext</div>
    pattern = r'<div class="image-placeholder">([^<]+)</div>'
    return list(re.finditer(pattern, html_content))

def convert_background_to_img(html_content):
    """Convert background-image style placeholders to img tags."""
    # Match: <div class="image-placeholder" style="background-image: url('path/to/image.jpg')"></div>
    # Also handles multi-line versions with </div> on next line
    pattern = r'<div class="image-placeholder" style="background-image: url\([\'"]([^\'"]+)[\'"]\)">\s*</div>'
    
    def replace_with_img(match):
        img_path = match.group(1)
        # Extract filename for alt text
        alt_text = Path(img_path).stem.replace('_', ' ').replace('-', ' ').title()
        return f'<div class="image-placeholder"><img src="{img_path}" alt="{alt_text}"></div>'
    
    new_content = re.sub(pattern, replace_with_img, html_content)
    changes_made = new_content != html_content
    return new_content, changes_made

def update_footer(html_content, is_blog=False):
    """Update the footer to the standard template."""
    # Match footer tag and all its contents, including any leading whitespace
    footer_pattern = r'[ \t]*<footer>[\s\S]*?</footer>'
    standard = STANDARD_FOOTER_BLOG if is_blog else STANDARD_FOOTER
    
    new_content, count = re.subn(footer_pattern, standard, html_content)
    return new_content, count > 0

def update_header(html_content, is_blog=False, is_index=False):
    """Update the header to the standard template."""
    # Match header tag and all its contents, including any leading whitespace
    # (handles both <header> and <header class="scrolled">)
    header_pattern = r'[ \t]*<header[^>]*>[\s\S]*?</header>'
    
    if is_blog:
        standard = STANDARD_HEADER_BLOG
    elif is_index:
        standard = STANDARD_HEADER_INDEX
    else:
        standard = STANDARD_HEADER
    
    new_content, count = re.subn(header_pattern, standard, html_content)
    return new_content, count > 0

def update_partners_section(html_content, available_images):
    """Update the partners/customers section with scrolling logos."""
    # Use explicit markers for reliability
    partners_pattern = r'(<!-- PARTNERS_START -->)([\s\S]*?)(<!-- PARTNERS_END -->)'
    
    # Identify logo images
    logo_images = []
    for stem, filename in available_images.items():
        if 'logo' in stem:
             if filename not in [x[1] for x in logo_images]:
                 logo_images.append((stem, filename))
    
    if not logo_images:
        print("No logo images found for partners section.")
        return html_content, False

    # Sort for consistency
    logo_images.sort()

    # Generate images HTML
    images_html = ""
    for _, filename in logo_images:
        images_html += f'<img src="imgs/{filename}" alt="Partner Logo" class="partner-logo">\n'
    
    # Create a base set that is long enough to likely fill a screen width
    # Assuming avg logo width + gap ~ 200px. 1920px screen ~ 10 logos.
    base_set = images_html
    # Count occurrences of img tag to estimate count
    count = base_set.count('<img')
    
    # Repeat until we have at least 15 items in the base set to be safe
    while base_set.count('<img') < 40:
        base_set += images_html
        
    new_section_content = f"""
                <div class="partners-track">
                    <div class="slide-track">
                        {base_set}
                    </div>
                    <div class="slide-track">
                        {base_set}
                    </div>
                </div>
                """
    
    def replace_content(match):
        return f"{match.group(1)}{new_section_content}{match.group(3)}"
    
    new_content, count = re.subn(partners_pattern, replace_content, html_content)
    return new_content, count > 0

def update_html_file(html_path, available_images, dry_run=False, update_common=True):
    """Update placeholders and common elements in a single HTML file."""
    if not html_path.exists():
        return [], [], [], []
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    placeholder_updates = []
    common_updates = []
    conversion_updates = []
    partner_updates = []
    
    is_blog = html_path.parent.name == 'blog' and html_path.name != 'template.html'
    is_index = html_path.name == 'index.html' and not is_blog
    
    # Special handling for blog template: it lives in blog/ but is used to generate root pages
    # so it needs root-relative paths (no ../)
    if html_path.parent.name == 'blog' and html_path.name == 'template.html':
        is_blog = False
    
    # First, convert any existing background-image placeholders to img tags
    content, converted = convert_background_to_img(content)
    if converted:
        conversion_updates.append({
            'file': html_path.name,
            'type': 'conversion',
            'description': 'Converted background-image placeholders to img tags'
        })
    
    # Update placeholders
    placeholders = find_placeholders(content)
    
    for match in reversed(placeholders):  # Reverse to preserve positions
        placeholder_text = match.group(1).strip()
        placeholder_stem = Path(placeholder_text).stem.lower()
        placeholder_full = placeholder_text.lower()
        
        # Try to find matching image by stem (name without extension)
        # This allows the placeholder to specify any extension and still match
        matched_image = None
        if placeholder_stem in available_images:
            matched_image = available_images[placeholder_stem]
        elif placeholder_full in available_images:
            matched_image = available_images[placeholder_full]
        
        if matched_image:
            # Determine the relative path to imgs folder
            if is_blog:
                img_path = f"../imgs/{matched_image}"
            else:
                img_path = f"imgs/{matched_image}"
            
            # Create the replacement HTML using img tag for better sizing
            new_html = f'<div class="image-placeholder"><img src="{img_path}" alt="{placeholder_text}"></div>'
            
            # Replace in content
            content = content[:match.start()] + new_html + content[match.end():]
            
            placeholder_updates.append({
                'file': html_path.name,
                'type': 'placeholder',
                'placeholder': placeholder_text,
                'image': matched_image
            })
    
    # Update common elements if requested
    if update_common:
        # Update footer
        content, footer_updated = update_footer(content, is_blog)
        if footer_updated:
            common_updates.append({
                'file': html_path.name,
                'type': 'footer',
                'description': 'Updated to standard footer with legal links'
            })
        
        # Update header
        content, header_updated = update_header(content, is_blog, is_index)
        if header_updated:
            common_updates.append({
                'file': html_path.name,
                'type': 'header',
                'description': 'Updated to standard header'
            })
            
        # Update partners section (only for index.html for now)
        if is_index:
             content, partners_updated = update_partners_section(content, available_images)
             if partners_updated:
                 partner_updates.append({
                     'file': html_path.name,
                     'type': 'partners',
                     'description': 'Updated partners/customers scrolling section'
                 })
    
    # Only write if something changed
    if content != original_content and not dry_run:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return placeholder_updates, common_updates, conversion_updates, partner_updates

def run_update_placeholders(dry_run=False, skip_common=False):
    print("\n=== Updating Placeholders & Common Elements ===\n")
    if dry_run:
        print("--- DRY RUN MODE - No files will be modified ---\n")
    
    print("Scanning for images...")
    available_images = get_available_images()
    print(f"Found {len(available_images)//2} images in imgs folder\n")
    
    all_placeholder_updates = []
    all_common_updates = []
    all_conversion_updates = []
    all_partner_updates = []
    
    # Populate HTML_FILES dynamically
    print("Scanning for HTML files...")
    html_files_found = []
    
    # Scan root directory
    for file_path in SCRIPT_DIR.glob("*.html"):
        if file_path.name == "blog.html": # handled by build_blog.py mostly, but we might want to update common elements
            pass 
        html_files_found.append(file_path)
        
    print(f"Found {len(html_files_found)} HTML files in root.")

    for html_path in html_files_found:
        placeholder_updates, common_updates, conversion_updates, partner_updates = update_html_file(
            html_path, available_images, dry_run, not skip_common
        )
        all_placeholder_updates.extend(placeholder_updates)
        all_common_updates.extend(common_updates)
        all_conversion_updates.extend(conversion_updates)
        all_partner_updates.extend(partner_updates)
    
    # Also check blog folder
    blog_dir = SCRIPT_DIR / "blog"
    if blog_dir.exists():
        for html_file in blog_dir.glob("*.html"):
            placeholder_updates, common_updates, conversion_updates, partner_updates = update_html_file(
                html_file, available_images, dry_run, not skip_common
            )
            all_placeholder_updates.extend(placeholder_updates)
            all_common_updates.extend(common_updates)
            all_conversion_updates.extend(conversion_updates)
            all_partner_updates.extend(partner_updates)
    
    # Report results
    if all_conversion_updates:
        print("\nImage format conversions:" if not dry_run else "\nImage format conversions that would be made:")
        print("-" * 60)
        for update in all_conversion_updates:
            print(f"  {update['file']}: {update['description']}")
        print(f"Total: {len(all_conversion_updates)} file(s) converted")
    
    if all_placeholder_updates:
        print("\nPlaceholder updates:" if not dry_run else "\nPlaceholder updates that would be made:")
        print("-" * 60)
        for update in all_placeholder_updates:
            print(f"  {update['file']}: {update['placeholder']} -> {update['image']}")
        print(f"Total: {len(all_placeholder_updates)} placeholder(s)")
    else:
        print("\nNo placeholders found with matching images.")
    
    if all_common_updates:
        print("\nCommon element updates:" if not dry_run else "\nCommon element updates that would be made:")
        print("-" * 60)
        for update in all_common_updates:
            print(f"  {update['file']}: {update['type']} - {update['description']}")
        print(f"Total: {len(all_common_updates)} common element(s) updated")
    elif not skip_common:
        print("\nNo common element updates needed.")
    
    if all_partner_updates:
        print("\nPartner section updates:" if not dry_run else "\nPartner section updates that would be made:")
        print("-" * 60)
        for update in all_partner_updates:
            print(f"  {update['file']}: {update['description']}")
        print(f"Total: {len(all_partner_updates)} partner section(s) updated")

    if not all_placeholder_updates and not all_common_updates and not all_conversion_updates and not all_partner_updates:
        print("No updates were needed.")

# ==========================================
# Main Execution
# ==========================================

def main():
    dry_run = '--dry-run' in sys.argv
    skip_common = '--skip-common' in sys.argv
    
    # Always run build_blog first (unless dry_run, but even then we might want to see output?)
    # If dry_run, we probably shouldn't write files.
    # build_blog currently doesn't have a dry_run mode in its original implementation.
    # I should probably respect dry_run for build_blog too.
    
    if dry_run:
        print("=== DRY RUN MODE - No files will be modified ===\n")
    
    if not dry_run:
        run_build_blog()
    else:
         print("Skipping blog build in dry-run mode (blog build does not support dry-run yet)")

    # Then update placeholders
    run_update_placeholders(dry_run, skip_common)
    
    print("\n=== Build Complete ===")

if __name__ == "__main__":
    main()
