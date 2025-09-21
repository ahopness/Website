#!/usr/bin/env python3

"""
Static Site Generator Builder.
Processes HTML pages with templates and copies data files to the build directory.
Doesn't require any external packages.
"""

import shutil
import re
from pathlib import Path

class StaticSiteBuilder:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.data_dir = self.root_dir / "data"
        self.pages_dir = self.root_dir / "pages"
        self.templates_dir = self.root_dir / "templates"
        self.build_dir = self.root_dir / "build"
    
    def clean_build_dir(self):
        if self.build_dir.exists():
            # Remove contents instead of the entire directory to avoid breaking the server
            for item in self.build_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            print(f"Cleaned build directory: {self.build_dir}")
        else:
            self.build_dir.mkdir(exist_ok=True)
            print(f"Created build directory: {self.build_dir}")
    
    def copy_data_files(self):
        if not self.data_dir.exists():
            print("No data directory found, skipping data files...")
            return
        
        for item in self.data_dir.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(self.data_dir)
                dest_path = self.build_dir / rel_path
                
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(item, dest_path)
                print(f"Copied data file: {rel_path}")
    
    def extract_template_tag(self, content):
        match = re.match(r'^\s*<!--\s*TEMPLATE:\s*(\w+)\s*-->\s*\n?', content)
        if match:
            template_name = match.group(1)
            content_without_tag = re.sub(r'^\s*<!--\s*TEMPLATE:\s*\w+\s*-->\s*\n?', '', content)
            return template_name, content_without_tag
        return None, content
    
    def extract_background_tag(self, content):
        match = re.match(r'^\s*<!--\s*BACKGROUND:\s*([\w.-]+)\s*-->\s*\n?', content)
        if match:
            template_name = match.group(1)
            content_without_tag = re.sub(r'^\s*<!--\s*BACKGROUND:\s*[\w.-]+\s*-->\s*\n?', '', content)
            return template_name, content_without_tag
        return None, content
    
    def load_template(self, template_name):
        template_path = self.templates_dir / f"{template_name}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def process_page(self, page_path):
        page_name = page_path.stem
        
        with open(page_path, 'r', encoding='utf-8') as f:
            page_content = f.read()
        
        template_name, clean_content = self.extract_template_tag(page_content)
        backrgound_filename, clean_content = self.extract_background_tag(clean_content)
        
        if not template_name:
            print(f"No TEMPLATE tag found in {page_path.name}, skipping...")
            return
        if not backrgound_filename:
            print(f"No BACKGROUND tag found in {page_path.name}, skipping...")
            return
        
        try:
            template_content = self.load_template(template_name)
            
            pretty_page_name = page_name.replace('-', ' ').capitalize()
            if pretty_page_name == 'Index': pretty_page_name = "Home"
            final_content = template_content.replace('<!-- TITLE -->', pretty_page_name)

            final_content = final_content.replace('<!-- BACKGROUND -->', backrgound_filename)

            final_content = final_content.replace('<!-- CONTENT -->', clean_content)
            
            if page_name.lower() == 'index':
                # Index page goes to build root
                output_path = self.build_dir / "index.html"
            else:
                page_folder = self.build_dir / page_name
                page_folder.mkdir(exist_ok=True)
                output_path = page_folder / "index.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            print(f"Built page: {page_name} -> {output_path.relative_to(self.build_dir)}")
            
        except FileNotFoundError as e:
            print(f"Error processing {page_path.name}: {e}")
    
    def build_pages(self):
        if not self.pages_dir.exists():
            print("No pages directory found, skipping pages...")
            return
        
        html_files = list(self.pages_dir.glob("*.html"))
        if not html_files:
            print("No HTML files found in pages directory...")
            return
        
        for page_path in html_files:
            self.process_page(page_path)
    
    def build(self):
        print("Starting static site build...")
        
        if not self.templates_dir.exists():
            print("Templates directory not found! Please create the 'templates' folder.")
            return False
        
        try:
            self.clean_build_dir()
            self.copy_data_files()
            self.build_pages()
            
            print("Build completed successfully!")
            return True
            
        except Exception as e:
            print(f"Build failed: {e}")
            return False

if __name__ == "__main__":
    builder = StaticSiteBuilder()
    success = builder.build()
    exit(0 if success else 1)