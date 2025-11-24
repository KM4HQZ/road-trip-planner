#!/bin/bash
# Launch script for Road Trip Planner GUI
# This activates the virtual environment and runs the GUI

cd "$(dirname "$0")"
source venv/bin/activate
python3 gui_app.py
