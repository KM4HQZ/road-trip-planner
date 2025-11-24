"""Map viewer widget using QWebEngineView."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from pathlib import Path


class MapViewer(QWidget):
    """Widget for displaying Folium maps."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
    def load_map(self, html_path):
        """Load a map HTML file."""
        if Path(html_path).exists():
            url = QUrl.fromLocalFile(str(Path(html_path).absolute()))
            self.web_view.setUrl(url)
        else:
            self.web_view.setHtml(f'<h2>Map file not found: {html_path}</h2>')
    
    def load_html_content(self, html_content):
        """Load HTML content directly."""
        self.web_view.setHtml(html_content)
