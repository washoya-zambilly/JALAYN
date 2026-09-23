from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QPushButton

class FullOffsetTableDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_win = parent  
        self.setWindowTitle("Full Offset Table - Jalayn")
        self.resize(700, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Station (X)", "Half-Breadth (Y)", "Height (Z)", "Type"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers) 

        row = 0
        
        # 1. Add Station Data
        if hasattr(self.main_win, 'stations') and self.main_win.stations:
            for x in sorted(self.main_win.stations.keys()):
                pts = self.main_win.stations[x]
                for pt in pts:
                    table.insertRow(row)
                    tx = f"{x:.3f}"
                    ty = f"{pt[1]:.3f}"
                    tz = f"{pt[2]:.3f}"
                    
                    table.setItem(row, 0, QTableWidgetItem(tx))
                    table.setItem(row, 1, QTableWidgetItem(ty))
                    table.setItem(row, 2, QTableWidgetItem(tz))
                    table.setItem(row, 3, QTableWidgetItem("Station Point"))
                    row += 1
        
        # 2. Add Profile Data
        if hasattr(self.main_win, 'profile_points') and self.main_win.profile_points:
            for pt in self.main_win.profile_points:
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(f"{pt[0]:.3f}"))
                table.setItem(row, 1, QTableWidgetItem("0.000")) 
                table.setItem(row, 2, QTableWidgetItem(f"{pt[2]:.3f}"))
                table.setItem(row, 3, QTableWidgetItem("Profile/Stem-Stern"))
                row += 1

        # If Table None
        if row == 0:
            layout.addWidget(QLabel("No data available. Please add stations or profile points first."))
        else:
            layout.addWidget(QLabel(f"Total points in database: {row}"))
            layout.addWidget(table)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)