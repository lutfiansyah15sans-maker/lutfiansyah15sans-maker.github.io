import os
import re

html_content = open('index.html', 'r', encoding='utf-8').read()

# 1. Extract styles
style_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
styles = style_match.group(1) if style_match else ""
os.makedirs('assets/css', exist_ok=True)
with open('assets/css/style.css', 'w', encoding='utf-8') as f:
    f.write(styles.strip())

# 2. Extract scripts
scripts = []
for m in re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html_content, re.DOTALL):
    scripts.append(m.group(1))
main_js = "\n\n".join(scripts)

# Add component loading logic to main.js
component_loader = """
// --- COMPONENT LOADER ---
document.addEventListener('DOMContentLoaded', function() {
    // Determine the base path based on depth
    let depth = window.location.pathname.split('/').filter(p => p).length;
    // Assuming root is where index.html is, if we are in /word-to-pdf/index.html, depth is 1
    // But this can be tricky on local file systems or GitHub pages.
    // Let's use a simpler approach: finding the relative path to root by checking script src
    let scripts = document.getElementsByTagName('script');
    let basePath = '';
    for (let script of scripts) {
        if (script.src && script.src.includes('assets/js/main.js')) {
            let src = script.getAttribute('src');
            basePath = src.substring(0, src.indexOf('assets/js/main.js'));
            break;
        }
    }
    if (!basePath && window.location.protocol === 'file:') {
        // Fallback for local files if the above fails
        let pathMatches = window.location.pathname.match(/\\/(.*\\/)/);
        let count = (document.currentScript ? document.currentScript.getAttribute('src') : '').split('../').length - 1;
        basePath = '../'.repeat(count);
    }

    Promise.all([
        fetch(basePath + 'components/navbar.html').then(r => r.text()),
        fetch(basePath + 'components/footer.html').then(r => r.text())
    ]).then(([navbarHtml, footerHtml]) => {
        // Fix image paths in components
        navbarHtml = navbarHtml.replace(/src="([^"]+)"/g, 'src="' + basePath + '$1"');
        footerHtml = footerHtml.replace(/src="([^"]+)"/g, 'src="' + basePath + '$1"');
        
        let headerEl = document.querySelector('header');
        if(headerEl) headerEl.outerHTML = navbarHtml;
        else document.body.insertAdjacentHTML('afterbegin', navbarHtml);

        let footerEl = document.querySelector('footer');
        if(footerEl) footerEl.outerHTML = footerHtml;
        else document.body.insertAdjacentHTML('beforeend', footerHtml);

        // Re-initialize theme logic after components are loaded
        const themeToggleBtn = document.getElementById('theme-toggle');
        if(themeToggleBtn) {
            const themeIcon = themeToggleBtn.querySelector('i');
            if (localStorage.getItem('lajupdf_theme') === 'dark') {
                document.body.classList.add('dark-mode');
                if(themeIcon) themeIcon.classList.replace('fa-moon', 'fa-sun');
            }
            themeToggleBtn.addEventListener('click', () => {
                document.body.classList.toggle('dark-mode');
                if (document.body.classList.contains('dark-mode')) {
                    if(themeIcon) themeIcon.classList.replace('fa-moon', 'fa-sun');
                    localStorage.setItem('lajupdf_theme', 'dark');
                } else {
                    if(themeIcon) themeIcon.classList.replace('fa-sun', 'fa-moon');
                    localStorage.setItem('lajupdf_theme', 'light');
                }
            });
        }
        
        // Setup lang switcher again if needed
        const langBtn = document.getElementById('lang-btn');
        if(langBtn) {
            langBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                document.getElementById('lang-dropdown').classList.toggle('open');
                this.classList.toggle('open');
            });
            document.addEventListener('click', function() {
                const dropdown = document.getElementById('lang-dropdown');
                if(dropdown && dropdown.classList.contains('open')) {
                    dropdown.classList.remove('open');
                    langBtn.classList.remove('open');
                }
            });
        }
    }).catch(e => console.error('Error loading components:', e));
});
// ------------------------
"""
main_js = component_loader + main_js

os.makedirs('assets/js', exist_ok=True)
with open('assets/js/main.js', 'w', encoding='utf-8') as f:
    f.write(main_js.strip())

# 3. Extract header
header_match = re.search(r'<header>.*?</header>', html_content, re.DOTALL)
header_html = header_match.group(0) if header_match else "<header></header>"
os.makedirs('components', exist_ok=True)
with open('components/navbar.html', 'w', encoding='utf-8') as f:
    f.write(header_html)

# 4. Extract footer
footer_match = re.search(r'<footer>.*?</footer>', html_content, re.DOTALL)
footer_html = footer_match.group(0) if footer_match else "<footer></footer>"
with open('components/footer.html', 'w', encoding='utf-8') as f:
    f.write(footer_html)

# 5. Generate base HTML content without styles, inline scripts, header, and footer
html_clean = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="assets/css/style.css">', html_content, flags=re.DOTALL)
html_clean = re.sub(r'<script(?![^>]*src=)[^>]*>.*?</script>', '', html_clean, flags=re.DOTALL)
html_clean = re.sub(r'<header>.*?</header>', '<header></header>', html_clean, flags=re.DOTALL)
html_clean = re.sub(r'<footer>.*?</footer>', '<footer></footer>', html_clean, flags=re.DOTALL)

# Insert the main.js script tag before </body>
html_clean = html_clean.replace('</body>', '    <script src="assets/js/main.js"></script>\n</body>')

# Save updated index.html
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_clean)

# 6. Tools and Pages
tools = [
    'word-to-pdf', 'excel-to-pdf', 'pptx-to-pdf', 'image-to-pdf',
    'jpg-to-png', 'merge-pdf', 'pdf-to-word', 'pdf-to-excel',
    'pdf-to-pptx', 'pdf-to-image', 'png-to-jpg', 'remove-background',
    'compress-pdf', 'split-pdf', 'pdf-to-text'
]

for tool in tools:
    os.makedirs(tool, exist_ok=True)
    # Adjust paths for depth 1
    tool_html = html_clean.replace('href="assets/css/style.css"', 'href="../assets/css/style.css"')
    tool_html = tool_html.replace('src="assets/js/main.js"', 'src="../assets/js/main.js"')
    # Also fix favicon and images that might be in the root directory in head
    tool_html = re.sub(r'href="([^"]+\.png)"', r'href="../\1"', tool_html)
    tool_html = re.sub(r'src="([^"]+\.png)"', r'src="../\1"', tool_html)

    with open(f'{tool}/index.html', 'w', encoding='utf-8') as f:
        f.write(tool_html)

print("Refactoring completed successfully.")
