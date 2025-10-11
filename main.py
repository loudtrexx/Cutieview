import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QScrollArea,
    QFileDialog,
    QLineEdit,
    QHBoxLayout,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import configparser
from functions import populate_thumbnails, FlowLayout, start_qtimer, stop_qtimer

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
        self.setGeometry(400, 400, 480, 320)

        # Create a label to display path the wallpapers are loaded from
        self.label = QLabel(f'Current Path: {wallpaper_path}', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.label.setFont(QFont('DejaVu Sans', 12))

        # Create a button to open the settings window
        self.button = QPushButton('Settings', self)
        self.button.clicked.connect(self.on_click)

        # Timer control button
        self.timer_button = QPushButton('Start', self)
        self.timer_button.clicked.connect(self.toggle_timer)
        self._timer = None

        # Thumbnail scroll area (wraps thumbnails)
        self.thumb_scroll = QScrollArea(self)
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_container = QWidget()
        if FlowLayout is not None:
            self.thumbs_layout = FlowLayout(self.thumb_container, spacing=6)
        else:
            self.thumbs_layout = QHBoxLayout()
            self.thumbs_layout.setSpacing(6)
        self.thumb_container.setLayout(self.thumbs_layout)
        self.thumb_scroll.setWidget(self.thumb_container)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.thumb_scroll)

        # Interval controls placed above the bottom control bar (Start / Settings)
        self.rb5 = QRadioButton('5s', self)
        self.rb10 = QRadioButton('10s', self)
        self.rb15 = QRadioButton('15s', self)
        self.rb_group = QButtonGroup(self)
        self.rb_group.addButton(self.rb5, 5)
        self.rb_group.addButton(self.rb10, 10)
        self.rb_group.addButton(self.rb15, 15)

        self.custom_spin = QSpinBox(self)
        self.custom_spin.setRange(1, 3600)
        self.custom_spin.setValue(int(config.get('Settings', 'time_seconds', fallback='10')))

        saved = int(config.get('Settings', 'time_seconds', fallback='10'))
        if saved in (5, 10, 15):
            btn = self.rb_group.button(saved)
            if btn:
                btn.setChecked(True)
        else:
            self.custom_spin.setValue(saved)

        # Default to 10s if nothing selected yet
        if self.rb_group.checkedId() == -1:
            self.rb10.setChecked(True)

        def save_time():
            sel = self.get_interval_seconds()
            config['Settings']['interval_seconds'] = str(sel)
            with open('config.ini', 'w') as cfgfile:
                config.write(cfgfile)

        self.rb5.toggled.connect(save_time)
        self.rb10.toggled.connect(save_time)
        self.rb15.toggled.connect(save_time)
        self.custom_spin.valueChanged.connect(save_time)

        interval_h = QHBoxLayout()
        interval_h.addWidget(QLabel('Time in seconds:'))
        interval_h.addWidget(self.rb5)
        interval_h.addWidget(self.rb10)
        interval_h.addWidget(self.rb15)
        interval_h.addWidget(QLabel('Custom (s):'))
        interval_h.addWidget(self.custom_spin)

        layout.addLayout(interval_h)

        layout.addStretch()

        bottom_h = QHBoxLayout()
        bottom_h.addWidget(self.timer_button)
        bottom_h.addStretch()
        bottom_h.addWidget(self.button)
        layout.addLayout(bottom_h)

        self.setLayout(layout)

        # keep reference for child windows
        self.settings_window = None

        # Populate initial thumbnails if a path exists
        if wallpaper_path:
            try:
                populate_thumbnails(self.thumbs_layout, wallpaper_path)
            except Exception:
                pass

    def on_click(self):
        """Open (or focus) the settings window."""
        if self.settings_window is not None:
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return

        self.settings_window = SettingsWindow(parent=self)
        self.settings_window.show()

    def toggle_timer(self):
        """Start or stop a periodic thumbnail refresh timer."""
        if self._timer is None:
            # start timer to refresh thumbnails every 10s
            current_path = config.get('Settings', 'wallpaper_path', fallback='')
            if not current_path:
                return
            # determine interval (seconds) from settings or settings window
            try:
                if self.settings_window is not None:
                    seconds = self.settings_window.get_interval_seconds()
                else:
                    seconds = int(config.get('Settings', 'interval_seconds', fallback='10'))
            except Exception:
                seconds = 10
            interval_ms = max(1, int(seconds)) * 1000
            self._timer = start_qtimer(interval_ms, lambda: populate_thumbnails(self.thumbs_layout, current_path))
            self.timer_button.setText('Stop')
        else:
            stop_qtimer(self._timer)
            self._timer = None
            self.timer_button.setText('Start')


class SettingsWindow(QWidget):
    """Settings window with a folder browse control."""

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Settings — Cutieview')
        self.setGeometry(800, 200, 520, 120)

        lbl = QLabel('Current Path:', self)
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

    def get_interval_seconds(self) -> int:
        """Return currently selected interval in seconds (radio selection or custom)."""
        checked_id = self.rb_group.checkedId()
        if checked_id in (5, 10, 15) and self.rb_group.checkedButton() is not None:
            return checked_id
        return int(self.custom_spin.value())

    def browse_folder(self):
        """Open a directory chooser, update config and the main window label."""
        start_dir = config.get('Settings', 'wallpaper_path', fallback=os.path.expanduser('~')) or os.path.expanduser('~')
        directory = QFileDialog.getExistingDirectory(self, 'Select folder', start_dir)
        if not directory:
            return  # user cancelled

        # Update the config object and write to disk
        config['Settings']['wallpaper_path'] = directory
        with open('config.ini', 'w') as cfgfile:
            config.write(cfgfile)

        # Update the UI
        self.path_edit.setText(directory)
        if self.parent is not None and hasattr(self.parent, 'label'):
            self.parent.label.setText(f'Path: {directory}')
            try:
                populate_thumbnails(self.parent.thumbs_layout, directory)
            except Exception:
                pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleApp()
    window.show()
    sys.exit(app.exec_())
