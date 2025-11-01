"""
Development Server for Static Site Generator.
Serves the built site content on localhost:1313 with hot reloading.
Needs watchdog packaged, install with 'pip install watchdog'.
"""

import os
import sys
import time
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if args and len(args) > 1:
            status_code = args[1]
            if status_code.startswith('2'):
                return
        print(f"[{self.address_string()}] {format % args}")
    
    def do_GET(self):
        try:
            super().do_GET()
        except (FileNotFoundError, OSError, PermissionError):
            print("Build in progress, serving rebuild page...")
            self.send_response(503)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Refresh', '2')
            self.end_headers()
            rebuild_html = '''<!DOCTYPE html>
<html><head><title>Site Rebuilding</title></head>
<body style="font-family: 'JetBrains Mono', monospace; text-align: center; padding: 50px; background: #000; color: #f5f5dc;">
    <h2>Site Rebuilding...</h2>
    <p>The site is being rebuilt. This page will refresh automatically.</p>
    <script>setTimeout(() => location.reload(), 2000);</script>
</body></html>'''
            self.wfile.write(rebuild_html.encode('utf-8'))


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server_instance):
        self.server = server_instance
        self.last_rebuild = 0
        self.debounce_seconds = 1
    
    def should_rebuild(self, event_path):
        path = Path(event_path)
        
        if 'build' in path.parts:
            return False
            
        relevant_extensions = {'.html', '.css', '.js', '.py'}
        if path.suffix not in relevant_extensions:
            return False
        
        current_time = time.time()
        if current_time - self.last_rebuild < self.debounce_seconds:
            return False
            
        return True
    
    def on_modified(self, event):
        if not event.is_directory and self.should_rebuild(event.src_path):
            self.trigger_rebuild(event.src_path)
    
    def on_created(self, event):
        if not event.is_directory and self.should_rebuild(event.src_path):
            self.trigger_rebuild(event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory and self.should_rebuild(event.src_path):
            self.trigger_rebuild(event.src_path)
    
    def trigger_rebuild(self, changed_file):
        self.last_rebuild = time.time()
        print(f"File changed: {changed_file}")
        print("Rebuilding site...")
        
        rebuild_thread = threading.Thread(target=self.server.rebuild_site)
        rebuild_thread.daemon = True
        rebuild_thread.start()


class StaticSiteServer:
    def __init__(self, port=1313, build_dir="build", enable_hot_reload=True, skip_initial_build=False):
        self.port = port
        self.build_dir = Path(build_dir)
        self.server = None
        self.enable_hot_reload = enable_hot_reload
        self.file_observer = None
        self.project_root = Path.cwd()
        self.skip_initial_build = skip_initial_build
    
    def check_build_dir(self):
        if not self.build_dir.exists():
            print(f"Build directory '{self.build_dir}' not found!")
            print("Please run 'python builder.py' first to build the site.")
            return False
        
        if not self.build_dir.is_dir():
            print(f"'{self.build_dir}' exists but is not a directory!")
            return False
        
        index_file = self.build_dir / "index.html"
        if not index_file.exists():
            print(f"No index.html found in '{self.build_dir}'")
            print("The site might not have a homepage.")
        
        return True
    
    def rebuild_site(self):
        try:
            from builder import StaticSiteBuilder
            builder = StaticSiteBuilder(self.project_root)
            success = builder.build()
            
            if success:
                print("Site rebuilt successfully!")
            else:
                print("Site rebuild failed!")
                
        except ImportError:
            print("Could not import builder.py")
        except Exception as e:
            print(f"Error during rebuild: {e}")
    
    def setup_hot_reload(self):
        if not self.enable_hot_reload:
            return
            
        try:
            event_handler = FileChangeHandler(self)
            self.file_observer = Observer()
            
            watch_dirs = ['pages', 'templates', 'data']
            for dir_name in watch_dirs:
                watch_path = self.project_root / dir_name
                if watch_path.exists():
                    self.file_observer.schedule(event_handler, str(watch_path), recursive=True)
                    print(f"Watching {dir_name}/ for changes...")
            
            self.file_observer.start()
            print("Hot reloading enabled!")
            
        except Exception as e:
            print(f"Could not setup hot reloading: {e}")
            print("Hot reloading will be disabled.")
            self.enable_hot_reload = False
    
    def cleanup_hot_reload(self):
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            print("File watching stopped")
    
    def start_server(self):
        if not self.skip_initial_build:
            print("Building site on startup...")
            self.rebuild_site()
            print()
        
        if not self.check_build_dir():
            return False
        
        os.chdir(self.project_root)
        self.setup_hot_reload()
        
        original_cwd = os.getcwd()
        os.chdir(self.build_dir)
        
        try:
            self.server = HTTPServer(('localhost', self.port), QuietHTTPRequestHandler)
            server_url = f"http://localhost:{self.port}"
            
            print(f"Starting development server...")
            print(f"Serving files from: {self.build_dir.absolute()}")
            print(f"Server running at: {server_url}")
            if self.enable_hot_reload:
                print(f"Hot reloading is active - changes will trigger rebuilds")
            print(f"Press Ctrl+C to stop the server")
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print(f"\nServer stopped by user")
            return True
        except OSError as e:
            if e.errno == 48:
                print(f"Port {self.port} is already in use!")
                print(f"Try using a different port or stop the other server.")
            else:
                print(f"Error starting server: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
        finally:
            self.cleanup_hot_reload()
            os.chdir(original_cwd)
            if self.server:
                self.server.server_close()
    
    def stop_server(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Server stopped")
        self.cleanup_hot_reload()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Serve static site for development with hot reloading')
    parser.add_argument('--port', '-p', type=int, default=1313, 
                        help='Port to serve on (default: 1313)')
    parser.add_argument('--build-dir', '-d', default='build',
                        help='Build directory to serve (default: build)')
    parser.add_argument('--no-hot-reload', action='store_true',
                        help="Disable hot reloading")
    parser.add_argument('--skip-build', action='store_true',
                        help="Skip initial build on startup")
    
    args = parser.parse_args()
    
    server = StaticSiteServer(
        port=args.port, 
        build_dir=args.build_dir,
        enable_hot_reload=not args.no_hot_reload,
        skip_initial_build=args.skip_build
    )
    success = server.start_server()
    
    sys.exit(0 if success else 1)
