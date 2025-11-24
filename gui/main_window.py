"""Main window for the Road Trip Planner GUI."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMenuBar, QMenu,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon
import sys
from pathlib import Path

from .trip_form import TripForm
from .results_panel import ResultsPanel
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('RoadTripPlanner', 'TripPlanner')
        self.current_trip_data = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Road Trip Planner 🚗🐾')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.trip_form = TripForm(self)
        self.results_panel = ResultsPanel(self)
        
        self.tabs.addTab(self.trip_form, "Plan Trip")
        self.tabs.addTab(self.results_panel, "Results")
        
        # Initially disable results tab
        self.tabs.setTabEnabled(1, False)
        
        # Connect signals
        self.trip_form.trip_completed.connect(self.on_trip_completed)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready to plan your trip!')
        
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open Trip Data...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_trip_data)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        settings_action = QAction('&Settings...', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        clear_cache_action = QAction('Clear Location Cache', self)
        clear_cache_action.triggered.connect(self.clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction('&Documentation', self)
        docs_action.triggered.connect(self.show_docs)
        help_menu.addAction(docs_action)
        
    def on_trip_completed(self, trip_data):
        """Handle trip planning completion."""
        self.current_trip_data = trip_data
        self.results_panel.load_trip_data(trip_data)
        self.tabs.setTabEnabled(1, True)
        self.tabs.setCurrentIndex(1)
        self.status_bar.showMessage('Trip planning completed!', 5000)
        
    def open_trip_data(self):
        """Open a saved trip data JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open Trip Data',
            str(Path.home() / 'Documents' / 'road-trip' / 'trip routes'),
            'JSON Files (*.json);;All Files (*)'
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    trip_data = json.load(f)
                self.on_trip_completed(trip_data)
                self.status_bar.showMessage(f'Loaded: {Path(file_path).name}', 5000)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Error',
                    f'Failed to load trip data:\n{str(e)}'
                )
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Settings were saved
            self.status_bar.showMessage('Settings saved', 3000)
    
    def clear_cache(self):
        """Clear the location cache."""
        cache_file = Path('location_cache.json')
        if cache_file.exists():
            reply = QMessageBox.question(
                self,
                'Clear Cache',
                'Are you sure you want to clear the location cache?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                cache_file.unlink()
                self.status_bar.showMessage('Cache cleared', 3000)
        else:
            QMessageBox.information(self, 'Cache', 'No cache file found.')
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            'About Road Trip Planner',
            '<h2>Road Trip Planner 🚗🐾</h2>'
            '<p>Version 1.0</p>'
            '<p>An intelligent road trip planning tool that automatically finds '
            'pet-friendly hotels, emergency vets, parks, restaurants, and attractions.</p>'
            '<p><b>Features:</b></p>'
            '<ul>'
            '<li>Pet-friendly hotel recommendations</li>'
            '<li>24/7 emergency veterinarians</li>'
            '<li>National parks and attractions</li>'
            '<li>Dog-friendly restaurants and parks</li>'
            '<li>GPX export for mobile navigation</li>'
            '</ul>'
            '<p>© 2025 - Licensed under CC BY-NC-SA 4.0</p>'
        )
    
    def show_docs(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            'Documentation',
            '<h3>Quick Start</h3>'
            '<ol>'
            '<li>Enter your origin and destination cities</li>'
            '<li>Optionally add via cities for a varied route</li>'
            '<li>Set your Google Places API key in Settings</li>'
            '<li>Click "Plan Trip" to generate your route</li>'
            '<li>View results and export GPX for mobile navigation</li>'
            '</ol>'
            '<p>For detailed documentation, see README.md in the project folder.</p>'
        )
