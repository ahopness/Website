"""
Static Site Generator Builder.
Processes HTML pages with Jinja2 templates and copies data files to the build directory.
"""

import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class StaticSiteBuilder:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.data_dir = self.root_dir / "data"
        self.pages_dir = self.root_dir / "pages"
        self.templates_dir = self.root_dir / "templates"
        self.build_dir = self.root_dir / "build"
        
        self.jinja_env = Environment(
            loader=FileSystemLoader([str(self.templates_dir), str(self.pages_dir)]),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
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
    
    def process_page(self, page_path):
        page_name = page_path.stem
        
        try:
            template = self.jinja_env.get_template(page_path.name)
            final_content = template.render()
            
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
        except TemplateNotFound as e:
            print(f"Error processing {page_path.name}: Template not found - {e}")
        except Exception as e:
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