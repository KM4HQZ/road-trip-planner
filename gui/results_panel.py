"""Results panel for displaying trip information."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QSplitter, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path

from .map_viewer import MapViewer


class ResultsPanel(QWidget):
    """Panel for displaying trip results and exporting files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trip_data = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Create splitter for map and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Map viewer
        self.map_viewer = MapViewer()
        splitter.addWidget(self.map_viewer)
        
        # Right side: Trip details and export
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Trip summary
        summary_group = QGroupBox('Trip Summary')
        self.summary_layout = QFormLayout()
        summary_group.setLayout(self.summary_layout)
        right_layout.addWidget(summary_group)
        
        # Details text
        details_label = QLabel('Trip Details')
        details_label.setStyleSheet('font-weight: bold; margin-top: 10px;')
        right_layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        right_layout.addWidget(self.details_text)
        
        # Export buttons
        export_group = QGroupBox('Export')
        export_layout = QVBoxLayout()
        
        self.open_map_btn = QPushButton('Open Map in Browser')
        self.open_map_btn.clicked.connect(self.open_map_in_browser)
        export_layout.addWidget(self.open_map_btn)
        
        self.export_gpx_btn = QPushButton('Export GPX for Navigation')
        self.export_gpx_btn.clicked.connect(self.export_gpx)
        export_layout.addWidget(self.export_gpx_btn)
        
        self.export_summary_btn = QPushButton('Export Summary (Markdown)')
        self.export_summary_btn.clicked.connect(self.export_summary)
        export_layout.addWidget(self.export_summary_btn)
        
        self.export_data_btn = QPushButton('Export Data (JSON)')
        self.export_data_btn.clicked.connect(self.export_data)
        export_layout.addWidget(self.export_data_btn)
        
        export_group.setLayout(export_layout)
        right_layout.addWidget(export_group)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes (70% map, 30% details)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
        
    def load_trip_data(self, trip_data):
        """Load trip data and display results."""
        self.trip_data = trip_data
        
        # Get config to determine what was exported
        config = trip_data.get('config', {})
        output_files = trip_data.get('output_files', {})
        
        # Show/hide export buttons based on what was generated
        self.open_map_btn.setVisible('map' in output_files)
        self.export_gpx_btn.setVisible('gpx' in output_files)
        self.export_summary_btn.setVisible('summary' in output_files)
        self.export_data_btn.setVisible('data' in output_files)
        
        # Load map if available
        map_file = output_files.get('map')
        if map_file and Path(map_file).exists():
            self.map_viewer.load_map(map_file)
        
        # Update summary
        self.clear_summary()
        self.add_summary_row('Origin', trip_data.get('origin', 'N/A'))
        self.add_summary_row('Destination', trip_data.get('destination', 'N/A'))
        
        if trip_data.get('via_cities'):
            via_text = ', '.join(trip_data['via_cities'])
            self.add_summary_row('Via Cities', via_text)
        
        self.add_summary_row('Distance', f"{trip_data.get('total_distance_miles', 0):.1f} miles")
        
        duration_h = trip_data.get('total_duration_hours', 0)
        duration_text = f"{int(duration_h)}h {int((duration_h % 1) * 60)}m"
        self.add_summary_row('Driving Time', duration_text)
        
        self.add_summary_row('Major Stops', str(len(trip_data.get('major_stops', []))))
        
        # Only show hotel/vet counts if they were searched
        if config.get('search_hotels', True):
            self.add_summary_row('Hotels Found', str(len(trip_data.get('hotels', {}))))
        if config.get('search_vets', True):
            self.add_summary_row('Emergency Vets', str(len(trip_data.get('vets', {}))))
        
        # Update details
        details = []
        details.append(f"# Trip Summary\n")
        details.append(f"Generated: {trip_data.get('generated_at', 'N/A')}\n\n")
        
        details.append(f"## Major Stops ({len(trip_data.get('major_stops', []))})\n")
        for stop in trip_data.get('major_stops', []):
            details.append(f"- {stop.get('name')}")
            if stop.get('wikivoyage_url'):
                details.append(f"  (Travel guide available)")
            details.append("\n")
        
        # Only show hotels if searched
        if config.get('search_hotels', True) and trip_data.get('hotels'):
            details.append(f"\n## Hotels ({len(trip_data.get('hotels', {}))})\n")
            for city, hotel in trip_data.get('hotels', {}).items():
                details.append(f"- **{city}**: {hotel.get('name')} ({hotel.get('rating')}⭐)\n")
        
        # Only show vets if searched
        if config.get('search_vets', True) and trip_data.get('vets'):
            details.append(f"\n## Emergency Veterinarians ({len(trip_data.get('vets', {}))})\n")
            for city, vet in trip_data.get('vets', {}).items():
                hours = "24/7" if vet.get('is_24_hours') else "Regular hours"
                details.append(f"- **{city}**: {vet.get('name')} ({hours})\n")
        
        # Attractions - only show categories that were searched
        attractions = trip_data.get('attractions', {})
        searched_attractions = {}
        
        category_config_map = {
            'national_parks': 'search_national_parks',
            'monuments': 'search_monuments',
            'parks': 'search_parks',
            'museums': 'search_museums',
            'restaurants': 'search_restaurants',
            'dog_parks': 'search_dog_parks',
            'viewpoints': 'search_viewpoints',
            'ev_chargers': 'search_ev_chargers'
        }
        
        for category, items in attractions.items():
            config_key = category_config_map.get(category)
            if config_key and config.get(config_key, True) and items:
                searched_attractions[category] = items
        
        if searched_attractions:
            total_attractions = sum(len(v) for v in searched_attractions.values())
            details.append(f"\n## Attractions ({total_attractions})\n")
            for category, items in searched_attractions.items():
                details.append(f"- {category.replace('_', ' ').title()}: {len(items)}\n")
        
        self.details_text.setMarkdown(''.join(details))
        
    def clear_summary(self):
        """Clear the summary form."""
        while self.summary_layout.rowCount() > 0:
            self.summary_layout.removeRow(0)
    
    def add_summary_row(self, label, value):
        """Add a row to the summary."""
        value_label = QLabel(str(value))
        value_label.setWordWrap(True)
        self.summary_layout.addRow(f"{label}:", value_label)
    
    def open_map_in_browser(self):
        """Open the HTML map in the default browser."""
        if not self.trip_data:
            return
            
        map_file = self.trip_data.get('output_files', {}).get('map')
        if map_file and Path(map_file).exists():
            import webbrowser
            import platform
            import subprocess
            
            # On macOS, use 'open' command directly to avoid PATH issues
            if platform.system() == 'Darwin':
                try:
                    subprocess.run(['/usr/bin/open', str(Path(map_file).absolute())], check=True)
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'Could not open browser: {e}')
            else:
                webbrowser.open(f'file://{Path(map_file).absolute()}')
        else:
            QMessageBox.warning(self, 'File Not Found', 'Map file not found.')
    
    def export_gpx(self):
        """Export/copy GPX file to user-chosen location."""
        if not self.trip_data:
            return
            
        gpx_file = self.trip_data.get('output_files', {}).get('gpx')
        if not gpx_file or not Path(gpx_file).exists():
            QMessageBox.warning(self, 'File Not Found', 'GPX file not found.')
            return
        
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save GPX File',
            str(Path.home() / 'Downloads' / Path(gpx_file).name),
            'GPX Files (*.gpx);;All Files (*)'
        )
        
        if dest_path:
            import shutil
            shutil.copy2(gpx_file, dest_path)
            QMessageBox.information(
                self,
                'Export Successful',
                f'GPX file saved to:\n{dest_path}\n\n'
                'You can now transfer this to your phone for navigation!'
            )
    
    def export_summary(self):
        """Export/copy summary markdown file."""
        if not self.trip_data:
            return
            
        summary_file = self.trip_data.get('output_files', {}).get('summary')
        if not summary_file or not Path(summary_file).exists():
            QMessageBox.warning(self, 'File Not Found', 'Summary file not found.')
            return
        
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Summary',
            str(Path.home() / 'Documents' / Path(summary_file).name),
            'Markdown Files (*.md);;All Files (*)'
        )
        
        if dest_path:
            import shutil
            shutil.copy2(summary_file, dest_path)
            QMessageBox.information(self, 'Export Successful', f'Summary saved to:\n{dest_path}')
    
    def export_data(self):
        """Export/copy trip data JSON file."""
        if not self.trip_data:
            return
            
        data_file = self.trip_data.get('output_files', {}).get('data')
        if not data_file or not Path(data_file).exists():
            QMessageBox.warning(self, 'File Not Found', 'Data file not found.')
            return
        
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Trip Data',
            str(Path.home() / 'Documents' / Path(data_file).name),
            'JSON Files (*.json);;All Files (*)'
        )
        
        if dest_path:
            import shutil
            shutil.copy2(data_file, dest_path)
            QMessageBox.information(self, 'Export Successful', f'Trip data saved to:\n{dest_path}')
