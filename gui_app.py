#!/usr/bin/env python3
"""
Road Trip Planner - GUI Application
Launch the graphical user interface for the road trip planner.

Usage:
    python gui_app.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui import MainWindow


def main():
    """Launch the GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName('Road Trip Planner')
    app.setOrganizationName('RoadTripPlanner')
    app.setOrganizationDomain('github.com/KM4HQZ/road-trip-planner')
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
