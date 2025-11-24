"""Settings dialog for configuring the application."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt
from pathlib import Path
import os
import sys


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            'Configure your API keys and preferences.\n'
            'Changes will be saved to your .env file.'
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: gray; font-size: 10px; margin-bottom: 10px;')
        layout.addWidget(info_label)
        
        # Form
        form_layout = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText('Enter your Google Places API key')
        
        show_key_btn = QPushButton('Show')
        show_key_btn.setMaximumWidth(60)
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(show_key_btn)
        
        form_layout.addRow('Google Places API Key:', api_key_layout)
        
        # Help text
        help_label = QLabel(
            '<a href="https://console.cloud.google.com/">Get your API key from Google Cloud Console</a>'
        )
        help_label.setOpenExternalLinks(True)
        help_label.setStyleSheet('font-size: 10px; margin-bottom: 20px;')
        form_layout.addRow('', help_label)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_settings(self):
        """Load current settings."""
        # Try to load from .env file
        env_file = self.get_env_file_path()
        if env_file.exists():
            from dotenv import dotenv_values
            config = dotenv_values(env_file)
            api_key = config.get('GOOGLE_PLACES_API_KEY', '')
            self.api_key_input.setText(api_key)
        else:
            # Check environment variable
            api_key = os.getenv('GOOGLE_PLACES_API_KEY', '')
            self.api_key_input.setText(api_key)
    
    def get_env_file_path(self):
        """Get the path to the .env file.
        
        When running as a bundled app, save to user's Documents folder.
        Otherwise, save to current directory.
        """
        # Check if we're running as a bundled app
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as bundled app - save to Documents/RoadTripPlanner
            docs_dir = Path.home() / 'Documents' / 'RoadTripPlanner'
            docs_dir.mkdir(parents=True, exist_ok=True)
            return docs_dir / '.env'
        else:
            # Running from source - use current directory
            return Path('.env')
    
    def save_settings(self):
        """Save settings to .env file."""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            reply = QMessageBox.question(
                self,
                'Empty API Key',
                'The API key is empty. Do you want to save anyway?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Save to .env file
        env_file = self.get_env_file_path()
        env_content = []
        
        # Read existing content
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if not line.startswith('GOOGLE_PLACES_API_KEY='):
                        env_content.append(line.rstrip())
        
        # Add/update API key
        env_content.append(f'GOOGLE_PLACES_API_KEY={api_key}')
        
        # Write back
        try:
            with open(env_file, 'w') as f:
                f.write('\n'.join(env_content))
                if env_content and not env_content[-1].endswith('\n'):
                    f.write('\n')
            
            # Update environment variable for current session
            os.environ['GOOGLE_PLACES_API_KEY'] = api_key
            
            QMessageBox.information(
                self,
                'Settings Saved',
                f'Settings saved to:\n{env_file}'
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                'Error Saving Settings',
                f'Could not save settings:\n{e}'
            )
    
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText('Hide')
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText('Show')
