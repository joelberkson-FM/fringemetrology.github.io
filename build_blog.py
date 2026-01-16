import os
import glob
import markdown
import yaml
import datetime

# Configuration
BLOG_DIR = 'blog'
POSTS_DIR = os.path.join(BLOG_DIR, 'posts')
TEMPLATE_FILE = os.path.join(BLOG_DIR, 'template.html')
BLOG_INDEX_FILE = 'blog.html'

def load_template():
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
    
    # Fix relative paths from template location
    # The template assumes it's in blog/, so standard relative paths work for posts in blog/ too.
    # checking template.html:
    # href="../css/style.css" -> works for blog/post.html
    # href="../imgs/favicon.ico" -> works for blog/post.html
    
    return output_html

def update_blog_index(posts):
    with open(BLOG_INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Sort posts by date desc
    posts.sort(key=lambda x: x['date'], reverse=True)
    
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
        
        date_str = date_obj.strftime('%B %d, %Y')
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
                    <article class="blog-card">
                        <div class="blog-card-image" style="background-image: url('{image}')"></div>
                        <div class="blog-card-content">
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

def main():
    if not os.path.exists(POSTS_DIR):
        print(f"No posts directory found at {POSTS_DIR}")
        return

    template = load_template()
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
        output_path = output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Saved {output_path}")
        processed_posts.append(metadata)

    update_blog_index(processed_posts)

if __name__ == "__main__":
    main()
