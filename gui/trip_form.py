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
            'waypoint_interval': self.waypoint_interval.value()
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
