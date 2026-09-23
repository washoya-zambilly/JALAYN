#training1_event.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMessageBox
from PySide6.QtWidgets import QMenu
import math

from training1_state import Qt_State

class Qt_Events:
    def __init__(self, canvas, state):
        self.canvas = canvas
        self.state = state

    #MENU RIGHT CLICK (FOR ADD & DELETE POINT)
    def handle_right_click(self, event):
        scene_pos = self.canvas.mapToScene(event.position().toPoint())
        self.state.right_click_segment = self.canvas.find_segment_near(scene_pos)
        self.state.right_click_profile_segment = self.canvas.find_profile_segment_near(scene_pos)
        self.state.right_click_point = self.canvas.find_point_near(scene_pos)

        menu = QMenu(self.canvas)
        
        if self.canvas.title.lower() == "side":
            prof_add = menu.addAction("Add Profile Point (Y=0)")
            prof_bet = menu.addAction("Add Profile Point Between")
            prof_del = menu.addAction("Delete Profile Point")
            menu.addSeparator()
            st_add = menu.addAction("Add Station Point")
            st_del = menu.addAction("Delete Station Point")
            
            action = menu.exec(event.globalPosition().toPoint())

            if action == prof_add:
                self.state.add_profile_point(scene_pos, self.canvas.title)
            elif action == prof_bet:
                self.state.add_profile_point_between()
            elif action == prof_del:
                self.state.delete_profile_point()
            elif action == st_add:
                self.state.add_point(scene_pos, self.canvas.title)
            elif action == st_del:
                self.state.delete_point()

        else:
            act_add = menu.addAction("Add Point")
            act_bet = menu.addAction("Add Point Between")
            act_del = menu.addAction("Delete Point")
            
            action = menu.exec(event.globalPosition().toPoint())

            if action == act_add:
                self.state.add_point(scene_pos, self.canvas.title)
            elif action == act_bet:
                self.state.add_point_between()
            elif action == act_del:
                self.state.delete_point()

    #---------- CLICK TO SELECT POINT -----------------
    def handle_mouse_press(self, event):
        scene_pos = self.canvas.mapToScene(event.position().toPoint())
        
        if event.button() == Qt.LeftButton:
            point_idx = self.canvas.find_point_near(scene_pos)
            
            if point_idx is not None:
                self.state.active_point_index = point_idx
                self.state.selected_index = point_idx     
                self.state.is_dragging = True
                
                self.canvas.main_window.table_widget.selectRow(point_idx)
            else:
                self.state.active_point_index = None
                self.state.selected_index = None
                self.state.is_dragging = False
                self.canvas.main_window.table_widget.clearSelection()

            self.canvas.update()

    def handle_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.state.is_dragging = False
            self.canvas.update()