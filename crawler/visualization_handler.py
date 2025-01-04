import os
from datetime import datetime
from typing import Dict, TextIO

class CrawlVisualizer:
    def __init__(self, log_file_path: str):
        self.log_file = log_file_path
        
    def initialize_log(self):
        """Initialize the log file with headers."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write("\n# Crawl Progress - Real-time Updates\n\n")
            f.write("*This visualization updates in real-time as pages are crawled*\n\n")

    def update_progress(self, graph: Dict, referrers: Dict, latest_url: str):
        """Update the visualization after each page visit."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            self._write_progress_header(f, graph, latest_url)
            self._write_tree_structure(f, graph)
            self._write_mermaid_diagram(f, graph)
            self._write_multiple_paths(f, referrers)

    def log_page_visit(self, url: str, title: str, screenshot_name: str, 
                       dimensions: Dict[str, int], processing_time: float):
        """Log information about a visited page."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n## Page: {url}\n")
            f.write(f"**Title**: {title}\n")
            f.write(f"**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Processing Time**: {processing_time:.2f} seconds\n")
            f.write(f"**Page Dimensions**: {dimensions['width']}x{dimensions['height']} pixels\n")
            f.write(f"**Screenshots Directory**: `{screenshot_name}`\n\n")
            
            # Add section information if available
            if 'sections' in dimensions:
                f.write(f"**Number of Sections**: {dimensions['sections']}\n")
                f.write("\n### Screenshots:\n")
                for i in range(dimensions['sections']):
                    f.write(f"- [Section {i + 1}]({screenshot_name}/section_{i + 1}.png)\n")

    def log_error(self, url: str, error: str):
        """Log an error that occurred during crawling."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n## ❌ Failed: {url}\n")
            f.write(f"**Error**: {error}\n\n---\n")

    def _write_tree_structure(self, file: TextIO, graph: Dict):
        """Write a tree-like structure of the crawled pages."""
        def _short_url(url):
            return url.replace('https://', '').replace('http://', '')[:50]

        def _write_node(url, indent=0, visited=None):
            if visited is None:
                visited = set()
            
            # Check for cyclic references
            if url in visited:
                file.write(f"{'    ' * indent}└── {_short_url(url)} (cyclic)\n")
                return
            visited.add(url)

            file.write(f"{'    ' * indent}└── {_short_url(url)}\n")
            if url in graph:
                for link in sorted(graph[url]['links'])[:5]:  # Limit to 5 children for readability
                    _write_node(link, indent + 1, visited.copy())

        # Start with the root (first URL added to the graph)
        if graph:
            root_url = next(iter(graph))
            _write_node(root_url)

    def _write_mermaid_diagram(self, file: TextIO, graph: Dict):
        """Write a Mermaid.js compatible diagram of the crawled pages."""
        def _node_id(url):
            # Create a unique, safe node ID
            return f"page_{hash(url) % 10000}"

        def _short_label(url):
            return url.replace('https://', '').replace('http://', '')[:20] + "..."

        # Prevent duplicate nodes
        written_nodes = set()
        for url in graph:
            node_id = _node_id(url)
            if node_id not in written_nodes:
                file.write(f'    {node_id}["{_short_label(url)}"]\n')
                written_nodes.add(node_id)

        # Prevent duplicate edges
        written_edges = set()
        for url, data in graph.items():
            source_id = _node_id(url)
            for link in list(data['links'])[:3]:
                target_id = _node_id(link)
                edge = f"{source_id}-->{target_id}"
                if edge not in written_edges:
                    file.write(f"    {edge}\n")
                    written_edges.add(edge)

    def _write_progress_header(self, file: TextIO, graph: Dict, latest_url: str):
        """Write the header section of the progress update."""
        file.write("\n---\n")  # Section separator
        file.write(f"\n## Current Progress - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"- Pages Crawled So Far: {len(graph)}\n")
        
        # Latest page crawled
        file.write(f"- Latest Page: {latest_url}\n")
        file.write(f"- Latest Title: {graph[latest_url]['title']}\n")
        
        # Interactive elements summary if available
        if 'interactive_elements' in graph[latest_url]:
            file.write("\n### Interactive Elements Found\n")
            for element_type, elements in graph[latest_url]['interactive_elements'].items():
                if elements:
                    file.write(f"- {element_type.capitalize()}: {len(elements)}\n")
        file.write("\n")

    def _write_multiple_paths(self, file: TextIO, referrers: Dict):
        """Write information about pages with multiple entry points."""
        multi_path_pages = {url: refs for url, refs in referrers.items() if len(refs) > 1}
        if multi_path_pages:
            file.write("### Pages with Multiple Entry Points\n")
            for url, refs in multi_path_pages.items():
                file.write(f"\n#### {url}\n")
                file.write("Accessible from:\n")
                for ref in sorted(refs):  # Sort for consistent output
                    file.write(f"- {ref}\n")
            file.write("\n")