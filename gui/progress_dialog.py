"""Progress dialog for trip planning."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt


class ProgressDialog(QDialog):
    """Dialog showing progress during trip planning."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Planning Trip...')
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel('Initializing...')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar (indeterminate since we don't know total steps)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Note label
        note_label = QLabel('This may take several minutes depending on trip complexity.')
        note_label.setStyleSheet('color: gray; font-size: 10px;')
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
    def update_progress(self, message):
        """Update progress message."""
        self.status_label.setText(message)
