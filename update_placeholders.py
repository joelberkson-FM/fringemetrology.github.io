#!/usr/bin/env python3
"""
update_placeholders.py - Updates image placeholders AND common elements in HTML files.

This script:
1. Scans HTML files for image-placeholder divs and updates them with matching images
2. Updates all footers and headers to match a standardized template

Usage:
    python update_placeholders.py [--dry-run]
    
Options:
    --dry-run    Show what would be changed without making modifications
"""

import os
import re
import sys
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
IMGS_DIR = SCRIPT_DIR / "imgs"
HTML_FILES = [] # Will be populated dynamically

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.avif'}


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
    # Match footer tag and all its contents
    footer_pattern = r'<footer>[\s\S]*?</footer>'
    standard = STANDARD_FOOTER_BLOG if is_blog else STANDARD_FOOTER
    
    new_content, count = re.subn(footer_pattern, standard, html_content)
    return new_content, count > 0

def update_header(html_content, is_blog=False, is_index=False):
    """Update the header to the standard template."""
    # Match header tag and all its contents (handles both <header> and <header class="scrolled">)
    header_pattern = r'<header[^>]*>[\s\S]*?</header>'
    
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
    common_updates = []
    conversion_updates = []
    partner_updates = []
    
    is_blog = 'blog' in str(html_path) and html_path.name != 'template.html'
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

def main():
    dry_run = '--dry-run' in sys.argv
    skip_common = '--skip-common' in sys.argv
    
    if dry_run:
        print("=== DRY RUN MODE - No files will be modified ===\n")
    
    print("Scanning for images...")
    available_images = get_available_images()
    print(f"Found {len(available_images)//2} images in imgs folder\n")
    
    all_placeholder_updates = []
    all_common_updates = []
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
        print("Image format conversions:" if not dry_run else "Image format conversions that would be made:")
        print("-" * 60)
        for update in all_conversion_updates:
            print(f"  {update['file']}: {update['description']}")
        print(f"Total: {len(all_conversion_updates)} file(s) converted\n")
    
    if all_placeholder_updates:
        print("Placeholder updates:" if not dry_run else "Placeholder updates that would be made:")
        print("-" * 60)
        for update in all_placeholder_updates:
            print(f"  {update['file']}: {update['placeholder']} -> {update['image']}")
        print(f"Total: {len(all_placeholder_updates)} placeholder(s)\n")
    else:
        print("No placeholders found with matching images.\n")
    
    if all_common_updates:
        print("Common element updates:" if not dry_run else "Common element updates that would be made:")
        print("-" * 60)
        for update in all_common_updates:
            print(f"  {update['file']}: {update['type']} - {update['description']}")
        print(f"Total: {len(all_common_updates)} common element(s) updated\n")
    elif not skip_common:
        print("No common element updates needed.\n")
    
    if all_partner_updates:
        print("Partner section updates:" if not dry_run else "Partner section updates that would be made:")
        print("-" * 60)
        for update in all_partner_updates:
            print(f"  {update['file']}: {update['description']}")
        print(f"Total: {len(all_partner_updates)} partner section(s) updated\n")

    if not all_placeholder_updates and not all_common_updates and not all_conversion_updates and not all_partner_updates:
        print("No updates were needed.")

if __name__ == "__main__":
    main()
