import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle('Cutieview')
        self.setGeometry(400, 400, 280, 280)

        # Create a label
        self.label = QLabel('Hi', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop)



        # Create a button
        self.button = QPushButton('Click Me', self)
        self.button.clicked.connect(self.on_click)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def on_click(self):
        self.label.setText('Button clicked!')

# Set up the application
app = QApplication(sys.argv)
window = SimpleApp()
window.show()

# Run the application's event loop
sys.exit(app.exec_())
