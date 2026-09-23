#training1_help_window.py
import sys
from PySide6.QtWidgets import (QApplication, QDialog, QWidget, QHBoxLayout, 
                               QVBoxLayout, QLineEdit, QListWidget, QTextBrowser, 
                               QLabel, QSplitter)
from PySide6.QtCore import Qt

class JalaynHelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jalayn - Help")
        self.resize(800, 500)
        
        self.setModal(False)

        # Content
        self.help_data = {
            "Station": (
                "<h3>How to Create a Station</h3>"
                "<p>Station can be made by clicking the 'Add Station' icon in the toolbar or 'Add Station' menu in the menu bar.</p>"
                "<b>Input X distance:</b> Input the X distance of the station, such as 0 for AP.<br>"
                "<b>Add Point:</b> Right-click on the Front View window, select 'Add Point' to create a station curve.<br>"
                "<b>Add Point Between:</b> Right-click on the created curve to add a new point.<br>"
                "<b>Delete Point:</b> Right-click on the created point to delete the point.<br>"
                "<h3>How to Select & Edit a Station</h3>"
                "Station can be selected by clicking the station name in the station list on the right side of the main window.<br>"
                "Select the station, and go to the offset table (in the main window) to edit the desired Y & Z values of the station coordinate.<br>"
                "Station also can be edited by dragging its points manually in the main window.<br>"
                "Station can only be edited if it is selected by the user and shown in <font color='red'><b>red color</b></font> in the Front View of the main window.<br>"
                "To rename a station, click on the station's name and change the name.<br>"
                "To delete a station, right-click on the station's name, and click the delete option."
            ),
            
            "Waterline": (
                "<h3>How to Create a Waterline</h3>"
                "<p>Waterline can be made by clicking the 'Add Waterline' icon in the toolbar or 'Add Waterline' menu in the menu bar.</p>"
                "<b>Input Z height:</b> Input the Z height of the waterline.<br>"
                "<b>Refresh Waterline:</b> Used to refresh the waterline shape after editing the station.<br>"
                "<p>To rename a waterline, click on the waterline's name and change the name.</p>"
                "To delete a waterline, right-click on the waterline's name, and click the delete option."
            ),

            "Buttockline": (
                "<h3>How to Create a Buttockline</h3>"
                "<p>Buttockline can be made by clicking the 'Add Buttockline' icon in the toolbar or 'Add Buttockline' menu in the menu bar.</p>"
                "<b>Input Y (breadth) distance:</b> Input the Y distance of the buttockline.<br>"
                "<b>Refresh Buttockline:</b> Used to refresh the buttockline shape after editing the station.<br>"
                "<p>To rename a buttockline, click on the buttockline's name and change the name.</p>"
                "To delete a buttockline, right-click on the buttockline's name, and click the delete option."
            ),

            "Profile": (
                "<h3>How to Create a Profile Center Line</h3>"
                "<p>Profile can be made by right-clicking and selecting the 'Add Point' option in the Front View window.</p>"
                "<b>Add Point Between:</b> Right-click on the created curve to add a new point.<br>"
                "<b>Delete Point:</b> Right-click on the created point to delete the point.<br>"
                "<p>Profile also can be edited by dragging its points manually in the main window or changing the point values via the offset table.</p>"
            ),

            "Preview Hull": (
                "<h3>How to View 3D Hull</h3>"
                "Select the 'Window' menu in the menu bar and select the 'Preview Hull' option to see the 3D Hull.<br>"
                "The dedicated icon in the toolbar can also be used to view the 3D Hull."
            ),

            "Ship Dimension": (
                "<h3>Input Ship Main Dimension</h3>"
                "<p>To enable the hydrostatic calculation, the user must input the ship's main dimensions below:</p>"
                "<b>Lpp:</b> Length between perpendiculars (From AP to FP)<br>"
                "<b>B:</b> Maximum breadth<br>"
                "<b>H:</b> Height of the main deck<br>"
                "<b>T:</b> Ship's draft"
            ),

            "Load & Save": (
                "<h3>Load & Save File</h3>"
                "<p>User can save the file as .json using menu 'Save As' & 'Save' in menu 'File'.</p>"
                "<br>While 'Load' option in the menu 'File' can be used to load the saved project file."
            ),

            "Export Result": (
                "<h3>Lines & 3D Model Output</h3>"
                "<p>User can export the created lines into dxf file using menu 'Window' in menu bar and selecting 'Export Lines' option.</p>"
                "<br>While created 3D model can be exported as vtk file using menu 'Window' in menu bar and selecting 'Export 3D' option."
            )
        }

        # MAIN LAYOUT
        main_layout = QVBoxLayout(self)

        # SEARCH BAR 
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Write the keyword... (example: Station, Waterline, Hull, etc)")
        self.search_input.textChanged.connect(self.filter_help_topics)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # SPLITTER
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # SIDEBAR LIST 
        self.topic_list = QListWidget()
        self.topic_list.addItems(self.help_data.keys())
        self.topic_list.currentTextChanged.connect(self.display_help_content)
        splitter.addWidget(self.topic_list)

        # TEXT DISPLAY PANEL
        self.content_display = QTextBrowser()
        self.content_display.setHtml("<i>Choose the menu to see the explanation.</i>")
        splitter.addWidget(self.content_display)

        splitter.setSizes([200, 600])

    def display_help_content(self, topic_name):
        if topic_name in self.help_data:
            self.content_display.setHtml(self.help_data[topic_name])

    def filter_help_topics(self, text):
        self.topic_list.clear()
        for topic in self.help_data.keys():
            if text.lower() in topic.lower() or text.lower() in self.help_data[topic].lower():
                self.topic_list.addItem(topic)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JalaynHelpWindow()
    window.show()
    sys.exit(app.exec())