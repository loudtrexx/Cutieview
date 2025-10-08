import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QFileDialog,
    QLineEdit,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import configparser

# Config initialization
config = configparser.ConfigParser()
config.read('config.ini')
if 'Settings' not in config:
    config['Settings'] = {'wallpaper_path': ''}

with open('config.ini', 'w') as configfile:
    config.write(configfile)

# Define main variables
wallpaper_path = config.get('Settings', 'wallpaper_path', fallback='')


class SimpleApp(QWidget):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle('Cutieview')
        self.setGeometry(400, 400, 360, 200)

        # Create a label to display path the wallpapers are loaded from
        self.label = QLabel(f'Current Path: {wallpaper_path}', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Make the main path label larger for readability
        self.label.setFont(QFont('DejaVu Sans', 12))

        # Create a button to open the settings window
        self.button = QPushButton('Settings', self)
        
        self.button.clicked.connect(self.on_click)

        # Set up the layout of the main window
        # Place the label at the top, add a stretch, then put the button at the bottom center
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        self.setLayout(layout)

        # keep reference for child windows
        self.settings_window = None

    def on_click(self):
        """Open (or focus) the settings window."""
        try:
            if self.settings_window is not None:
                self.settings_window.show()
                self.settings_window.raise_()
                self.settings_window.activateWindow()
                return
        except Exception:
            pass

        self.settings_window = SettingsWindow(parent=self)
        self.settings_window.show()


class SettingsWindow(QWidget):
    """Settings window with a folder browse control."""

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Settings — Cutieview')
        self.setGeometry(800, 200, 520, 120)

        lbl = QLabel('Default path:', self)
        lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Line edit to show the currently selected path
        current_path = config.get('Settings', 'wallpaper_path', fallback='')
        self.path_edit = QLineEdit(current_path, self)
        self.path_edit.setReadOnly(True)

        # Browse button
        browse_btn = QPushButton('Browse...', self)
        browse_btn.clicked.connect(self.browse_folder)
        browse_btn.setToolTip('Browse for a folder containing wallpapers')

        h = QHBoxLayout()
        h.addWidget(self.path_edit)
        h.addWidget(browse_btn)

        v = QVBoxLayout()
        v.addWidget(lbl)
        v.addLayout(h)
        v.addStretch()
        self.setLayout(v)

    def browse_folder(self):
        """Open a directory chooser, update config and the main window label."""
        start_dir = (
            config.get('Settings', 'wallpaper_path', fallback=os.path.expanduser('~'))
            or os.path.expanduser('~')
        )
        directory = QFileDialog.getExistingDirectory(self, 'Select folder', start_dir)
        if not directory:
            return  # user cancelled

        # Update the config object and write to disk
        config['Settings']['wallpaper_path'] = directory
        with open('config.ini', 'w') as cfgfile:
            config.write(cfgfile)

        # Update the UI
        self.path_edit.setText(directory)
        try:
            if self.parent is not None and hasattr(self.parent, 'label'):
                self.parent.label.setText(f'Path: {directory}')
        except Exception:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleApp()
    window.show()
    sys.exit(app.exec_())
