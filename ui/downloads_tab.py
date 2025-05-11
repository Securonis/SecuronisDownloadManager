#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QProgressBar, 
                            QHeaderView, QLabel, QInputDialog, QFileDialog, QLineEdit, QMenu)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
import os

class DownloadsTab(QWidget):
    def __init__(self, download_manager):
        super().__init__()
        
        self.download_manager = download_manager
        
        # Create UI elements
        self.init_ui()
        
        # Timer for updating download table
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_download_table)
        self.update_timer.start(1000)  # Update every second
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Button bar layout
        button_layout = QHBoxLayout()
        
        # New Download Button
        self.add_button = QPushButton("New Download")
        self.add_button.clicked.connect(self.add_download)
        button_layout.addWidget(self.add_button)
        
        # Stop Button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_download)
        button_layout.addWidget(self.stop_button)
        
        # Resume Button
        self.resume_button = QPushButton("Resume")
        self.resume_button.clicked.connect(self.resume_download)
        button_layout.addWidget(self.resume_button)
        
        # Delete Button
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_download)
        button_layout.addWidget(self.delete_button)
        
        # Clear Button
        self.clear_button = QPushButton("Clear Completed")
        self.clear_button.clicked.connect(self.clear_completed)
        button_layout.addWidget(self.clear_button)
        
        # Add right spacer
        button_layout.addStretch()
        
        # Add button bar to main layout
        main_layout.addLayout(button_layout)
        
        # Download table
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(8)
        self.download_table.setHorizontalHeaderLabels([
            "File Name", "Size", "Downloaded", "Speed", "Status", "Progress", "URL", "ID"
        ])
        self.download_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.download_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.download_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Hide the ID column
        self.download_table.setColumnHidden(7, True)
        
        # Set up context menu for the table
        self.download_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.download_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Add table to main layout
        main_layout.addWidget(self.download_table)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        # Active Downloads Count
        self.active_count_label = QLabel("Active Downloads: 0")
        stats_layout.addWidget(self.active_count_label)
        
        # Completed Downloads Count
        self.completed_count_label = QLabel("Completed: 0")
        stats_layout.addWidget(self.completed_count_label)
        
        # Total Download Speed
        self.total_speed_label = QLabel("Total Speed: 0 KB/s")
        stats_layout.addWidget(self.total_speed_label)
        
        # Add spacer
        stats_layout.addStretch()
        
        # Add statistics to main layout
        main_layout.addLayout(stats_layout)
        
    def add_download(self):
        # Create a non-resizable dialog to prevent bugs
        dialog = QInputDialog(self)
        dialog.setWindowTitle("New Download")
        dialog.setLabelText("Enter URL to download:")
        dialog.setTextValue("")
        dialog.setInputMode(QInputDialog.TextInput)
        
        # Make the dialog non-resizable
        dialog.setFixedSize(400, 150)
        
        if dialog.exec_() == QInputDialog.Accepted:
            url = dialog.textValue()
            if url:
                # Ask for save location
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save File",
                    self.download_manager.get_default_save_path(),
                    "All Files (*)"
                )
                
                if save_path:
                    # Start download using file's directory and name
                    self.download_manager.add_download(url, os.path.dirname(save_path), os.path.basename(save_path))
                    
                    # Update the UI immediately
                    self.update_download_table()
        
    def stop_download(self):
        # Get selected row(s)
        selected_rows = set(item.row() for item in self.download_table.selectedItems())
        
        if not selected_rows:
            return
        
        for row in selected_rows:
            # Get download ID from table
            download_id = self.download_table.item(row, 7).text()
            
            # Stop the download
            self.download_manager.stop_download(download_id)
        
        # Update the UI
        self.update_download_table()
        
    def resume_download(self):
        # Get selected row(s)
        selected_rows = set(item.row() for item in self.download_table.selectedItems())
        
        if not selected_rows:
            return
        
        for row in selected_rows:
            # Get download ID from table
            download_id = self.download_table.item(row, 7).text()
            
            # Resume the download
            self.download_manager.resume_download(download_id)
        
        # Update the UI
        self.update_download_table()
        
    def delete_download(self):
        # Get selected row(s)
        selected_rows = set(item.row() for item in self.download_table.selectedItems())
        
        if not selected_rows:
            return
        
        for row in selected_rows:
            # Get download ID from table
            download_id = self.download_table.item(row, 7).text()
            
            # Delete the download
            self.download_manager.delete_download(download_id)
        
        # Update the UI
        self.update_download_table()
        
    def clear_completed(self):
        # Ask download manager to clear completed downloads
        self.download_manager.clear_completed()
        
        # Update the UI
        self.update_download_table()
        
    @pyqtSlot()
    def update_download_table(self):
        # Get all downloads
        downloads = self.download_manager.get_all_downloads()
        
        # Update table rows
        self.download_table.setRowCount(len(downloads))
        
        # Statistics counters
        active_count = 0
        completed_count = 0
        total_speed = 0
        
        # Populate table
        for i, download in enumerate(downloads):
            # Update statistics
            if download.status == 'Downloading':
                active_count += 1
                total_speed += getattr(download, 'speed', 0)
            elif download.status == 'Completed':
                completed_count += 1
            
            # File name
            self.download_table.setItem(i, 0, QTableWidgetItem(download.filename))
            
            # Size
            size_text = self.format_size(download.size) if download.size > 0 else 'Unknown'
            self.download_table.setItem(i, 1, QTableWidgetItem(size_text))
            
            # Downloaded
            downloaded_text = self.format_size(download.downloaded)
            self.download_table.setItem(i, 2, QTableWidgetItem(downloaded_text))
            
            # Speed
            speed_text = self.format_speed(download.speed) if hasattr(download, 'speed') else '0 B/s'
            self.download_table.setItem(i, 3, QTableWidgetItem(speed_text))
            
            # Status
            self.download_table.setItem(i, 4, QTableWidgetItem(download.status))
            
            # Progress bar
            progress = 0
            if download.size > 0:
                progress = int((download.downloaded / download.size) * 100)
            
            progress_bar = QProgressBar()
            progress_bar.setValue(progress)
            self.download_table.setCellWidget(i, 5, progress_bar)
            
            # URL
            self.download_table.setItem(i, 6, QTableWidgetItem(download.url))
            
            # ID (hidden column)
            self.download_table.setItem(i, 7, QTableWidgetItem(download.id))
        
        # Update statistics labels
        self.active_count_label.setText(f"Active Downloads: {active_count}")
        self.completed_count_label.setText(f"Completed: {completed_count}")
        self.total_speed_label.setText(f"Total Speed: {self.format_speed(total_speed)}")
    
    def format_size(self, size_bytes):
        # Convert size to human-readable format
        if size_bytes < 0:
            return "Unknown"
            
        # Define size units
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0
        
        # Find appropriate unit
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
            
        return f"{size:.2f} {units[unit_index]}"
    
    def format_speed(self, speed_bytes):
        # Convert speed to human-readable format
        return f"{self.format_size(speed_bytes)}/s"
    
    def show_context_menu(self, position):
        """Shows context menu for the download table"""
        context_menu = QMenu(self)
        
        # Get selected items
        has_selection = len(self.download_table.selectedItems()) > 0
        
        # Add actions
        stop_action = context_menu.addAction("Stop")
        stop_action.triggered.connect(self.stop_download)
        stop_action.setEnabled(has_selection)
        
        resume_action = context_menu.addAction("Resume")
        resume_action.triggered.connect(self.resume_download)
        resume_action.setEnabled(has_selection)
        
        delete_action = context_menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_download)
        delete_action.setEnabled(has_selection)
        
        # Show the menu at the cursor position
        context_menu.exec_(self.download_table.mapToGlobal(position)) 