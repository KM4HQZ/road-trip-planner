"""Trip planning form widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QCheckBox,
    QLabel, QScrollArea, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
import os

from .progress_dialog import ProgressDialog
from .trip_planner_thread import TripPlannerThread


class TripForm(QWidget):
    """Form for entering trip parameters."""
    
    trip_completed = pyqtSignal(dict)  # Emits trip data when complete
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.via_city_widgets = []
        self.planner_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the form UI."""
        layout = QVBoxLayout(self)
        
        # Create scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # Title
        title = QLabel('Plan Your Pet-Friendly Road Trip')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        form_layout.addWidget(title)
        
        # Basic route group
        route_group = QGroupBox('Route')
        route_layout = QFormLayout()
        
        self.origin_input = QLineEdit()
        self.origin_input.setPlaceholderText('e.g., Atlanta, GA')
        route_layout.addRow('Origin:', self.origin_input)
        
        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText('e.g., Denver, CO')
        route_layout.addRow('Destination:', self.destination_input)
        
        route_group.setLayout(route_layout)
        form_layout.addWidget(route_group)
        
        # Via cities group
        via_group = QGroupBox('Via Cities (Optional)')
        self.via_layout = QVBoxLayout()
        
        add_via_btn = QPushButton('+ Add Via City')
        add_via_btn.clicked.connect(self.add_via_city)
        self.via_layout.addWidget(add_via_btn)
        
        via_group.setLayout(self.via_layout)
        form_layout.addWidget(via_group)
        
        # Options group
        options_group = QGroupBox('Options')
        options_layout = QFormLayout()
        
        self.stop_distance = QSpinBox()
        self.stop_distance.setRange(100, 500)
        self.stop_distance.setValue(250)
        self.stop_distance.setSuffix(' miles')
        options_layout.addRow('Stop Distance:', self.stop_distance)
        
        self.waypoint_interval = QSpinBox()
        self.waypoint_interval.setRange(50, 200)
        self.waypoint_interval.setValue(100)
        self.waypoint_interval.setSuffix(' miles')
        options_layout.addRow('Waypoint Interval:', self.waypoint_interval)
        
        self.roundtrip = QCheckBox('Return to origin (same route)')
        self.roundtrip.setToolTip('Use --via cities instead for a varied return route')
        options_layout.addRow('', self.roundtrip)
        
        options_group.setLayout(options_layout)
        form_layout.addWidget(options_group)
        
        # Search options group
        search_group = QGroupBox('Search Options')
        search_layout = QVBoxLayout()
        
        # Hotels subsection
        hotels_label = QLabel('<b>Accommodations</b>')
        search_layout.addWidget(hotels_label)
        
        self.search_hotels = QCheckBox('Search for hotels')
        self.search_hotels.setChecked(True)
        self.search_hotels.toggled.connect(self.on_hotels_toggled)
        search_layout.addWidget(self.search_hotels)
        
        self.pet_friendly_only = QCheckBox('Pet-friendly hotels only')
        self.pet_friendly_only.setChecked(True)
        self.pet_friendly_only.setEnabled(True)
        self.pet_friendly_only.setStyleSheet('margin-left: 20px;')
        search_layout.addWidget(self.pet_friendly_only)
        
        self.search_vets = QCheckBox('Search for 24/7 emergency vets')
        self.search_vets.setChecked(True)
        search_layout.addWidget(self.search_vets)
        
        # Attractions subsection
        attractions_label = QLabel('<b>Attractions & Points of Interest</b>')
        attractions_label.setStyleSheet('margin-top: 10px;')
        search_layout.addWidget(attractions_label)
        
        self.search_national_parks = QCheckBox('National parks')
        self.search_national_parks.setChecked(True)
        search_layout.addWidget(self.search_national_parks)
        
        self.search_monuments = QCheckBox('Monuments & memorials')
        self.search_monuments.setChecked(True)
        search_layout.addWidget(self.search_monuments)
        
        self.search_parks = QCheckBox('Parks')
        self.search_parks.setChecked(True)
        search_layout.addWidget(self.search_parks)
        
        self.search_museums = QCheckBox('Museums')
        self.search_museums.setChecked(True)
        search_layout.addWidget(self.search_museums)
        
        self.search_restaurants = QCheckBox('Dog-friendly restaurants')
        self.search_restaurants.setChecked(True)
        search_layout.addWidget(self.search_restaurants)
        
        self.search_dog_parks = QCheckBox('Dog parks')
        self.search_dog_parks.setChecked(True)
        search_layout.addWidget(self.search_dog_parks)
        
        self.search_viewpoints = QCheckBox('Scenic viewpoints')
        self.search_viewpoints.setChecked(True)
        search_layout.addWidget(self.search_viewpoints)
        
        self.search_ev_chargers = QCheckBox('EV charging stations')
        self.search_ev_chargers.setChecked(True)
        search_layout.addWidget(self.search_ev_chargers)
        
        search_group.setLayout(search_layout)
        form_layout.addWidget(search_group)
        
        # Export options group
        export_group = QGroupBox('Export Options')
        export_layout = QVBoxLayout()
        
        self.export_map = QCheckBox('Generate interactive HTML map')
        self.export_map.setChecked(True)
        export_layout.addWidget(self.export_map)
        
        self.export_gpx = QCheckBox('Generate GPX file for navigation apps')
        self.export_gpx.setChecked(True)
        export_layout.addWidget(self.export_gpx)
        
        self.export_data = QCheckBox('Generate JSON data file')
        self.export_data.setChecked(True)
        export_layout.addWidget(self.export_data)
        
        self.export_summary = QCheckBox('Generate markdown summary')
        self.export_summary.setChecked(True)
        export_layout.addWidget(self.export_summary)
        
        export_group.setLayout(export_layout)
        form_layout.addWidget(export_group)
        
        # Add stretch to push everything to the top
        form_layout.addStretch()
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # Bottom button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.plan_button = QPushButton('Plan Trip 🚗')
        self.plan_button.setMinimumHeight(40)
        self.plan_button.clicked.connect(self.plan_trip)
        button_layout.addWidget(self.plan_button)
        
        layout.addLayout(button_layout)
        
    def add_via_city(self):
        """Add a via city input field."""
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        via_input = QLineEdit()
        via_input.setPlaceholderText('e.g., Nashville, TN')
        h_layout.addWidget(via_input)
        
        remove_btn = QPushButton('Remove')
        remove_btn.clicked.connect(lambda: self.remove_via_city(container))
        h_layout.addWidget(remove_btn)
        
        # Insert before the "Add Via City" button
        self.via_layout.insertWidget(len(self.via_city_widgets), container)
        self.via_city_widgets.append(container)
        
    def remove_via_city(self, widget):
        """Remove a via city input field."""
        self.via_city_widgets.remove(widget)
        widget.deleteLater()
    
    def on_hotels_toggled(self, checked):
        """Enable/disable pet-friendly checkbox based on hotels checkbox."""
        self.pet_friendly_only.setEnabled(checked)
        
    def get_via_cities(self):
        """Get list of via cities from input fields."""
        via_cities = []
        for widget in self.via_city_widgets:
            line_edit = widget.findChild(QLineEdit)
            if line_edit and line_edit.text().strip():
                via_cities.append(line_edit.text().strip())
        return via_cities
        
    def plan_trip(self):
        """Start trip planning."""
        # Validate inputs
        origin = self.origin_input.text().strip()
        destination = self.destination_input.text().strip()
        
        if not origin:
            QMessageBox.warning(self, 'Input Required', 'Please enter an origin city.')
            return
            
        if not destination:
            QMessageBox.warning(self, 'Input Required', 'Please enter a destination city.')
            return
        
        # Check for API key
        api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not api_key:
            QMessageBox.critical(
                self,
                'API Key Required',
                'Google Places API key not found.\n\n'
                'Please set it in Settings (Tools → Settings) or in your .env file.'
            )
            return
        
        # Gather parameters
        via_cities = self.get_via_cities()
        params = {
            'origin': origin,
            'destination': destination,
            'via_cities': via_cities,
            'roundtrip': self.roundtrip.isChecked(),
            'target_hours': self.stop_distance.value() // 65,  # Approximate
            'waypoint_interval': self.waypoint_interval.value(),
            # Search options
            'search_hotels': self.search_hotels.isChecked(),
            'pet_friendly_only': self.pet_friendly_only.isChecked(),
            'search_vets': self.search_vets.isChecked(),
            'search_national_parks': self.search_national_parks.isChecked(),
            'search_monuments': self.search_monuments.isChecked(),
            'search_parks': self.search_parks.isChecked(),
            'search_museums': self.search_museums.isChecked(),
            'search_restaurants': self.search_restaurants.isChecked(),
            'search_dog_parks': self.search_dog_parks.isChecked(),
            'search_viewpoints': self.search_viewpoints.isChecked(),
            'search_ev_chargers': self.search_ev_chargers.isChecked(),
            # Export options
            'export_map': self.export_map.isChecked(),
            'export_gpx': self.export_gpx.isChecked(),
            'export_data': self.export_data.isChecked(),
            'export_summary': self.export_summary.isChecked()
        }
        
        # Create and start worker thread
        self.planner_thread = TripPlannerThread(params)
        
        # Create progress dialog
        self.progress_dialog = ProgressDialog(self)
        self.planner_thread.progress.connect(self.progress_dialog.update_progress)
        self.planner_thread.finished.connect(self.on_planning_finished)
        self.planner_thread.error.connect(self.on_planning_error)
        
        # Disable plan button
        self.plan_button.setEnabled(False)
        
        # Start planning
        self.planner_thread.start()
        self.progress_dialog.exec()
        
    def on_planning_finished(self, trip_data):
        """Handle successful trip planning."""
        self.plan_button.setEnabled(True)
        self.progress_dialog.close()
        self.trip_completed.emit(trip_data)
        
    def on_planning_error(self, error_msg):
        """Handle trip planning error."""
        self.plan_button.setEnabled(True)
        self.progress_dialog.close()
        QMessageBox.critical(
            self,
            'Error Planning Trip',
            f'An error occurred while planning your trip:\n\n{error_msg}'
        )
