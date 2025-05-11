#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QAction, QToolBar, 
                            QStatusBar, QFileDialog, QMessageBox, QVBoxLayout, 
                            QWidget, QMenu, QHBoxLayout, QPushButton, QInputDialog)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon

from ui.downloads_tab import DownloadsTab
from ui.privacy_tab import PrivacyTab
from ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self, download_manager, privacy_manager, settings_manager):
        super().__init__()
        
        self.download_manager = download_manager
        self.privacy_manager = privacy_manager
        self.settings_manager = settings_manager
        
        self.init_ui()
        
    def init_ui(self):
        # Main window properties
        self.setWindowTitle("Securonis Download Manager")
        self.setMinimumSize(900, 600)
        
        # Menu bar
        self.create_menu_bar()
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.downloads_tab = DownloadsTab(self.download_manager)
        self.privacy_tab = PrivacyTab(self.privacy_manager)
        self.settings_tab = SettingsTab(self.settings_manager)
        
        # Add tabs
        self.tabs.addTab(self.downloads_tab, "Downloads")
        self.tabs.addTab(self.privacy_tab, "Privacy")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # New download
        new_download_action = QAction("New Download", self)
        new_download_action.setShortcut("Ctrl+N")
        new_download_action.triggered.connect(self.new_download)
        file_menu.addAction(new_download_action)
        
        # Download from URL
        url_download_action = QAction("Download from URL", self)
        url_download_action.setShortcut("Ctrl+U")
        url_download_action.triggered.connect(self.download_from_url)
        file_menu.addAction(url_download_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Privacy menu
        privacy_menu = menu_bar.addMenu("Privacy")
        
        # Enable Tor Connection
        tor_action = QAction("Enable Tor Connection", self)
        tor_action.setCheckable(True)
        tor_action.triggered.connect(self.toggle_tor)
        privacy_menu.addAction(tor_action)
        
        # Enable VPN Connection
        vpn_action = QAction("Enable VPN Connection", self)
        vpn_action.setCheckable(True)
        vpn_action.triggered.connect(self.toggle_vpn)
        privacy_menu.addAction(vpn_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def new_download(self):
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
                    
                    # Update the downloads tab UI immediately
                    self.downloads_tab.update_download_table()
        
    def download_from_url(self):
        # Download from URL - same as new_download
        self.new_download()
        
    def stop_download(self):
        # Stop selected download in downloads tab
        self.downloads_tab.stop_download()
        
    def resume_download(self):
        # Resume selected download in downloads tab
        self.downloads_tab.resume_download()
        
    def delete_download(self):
        # Delete selected download in downloads tab
        self.downloads_tab.delete_download()
        
    def toggle_tor(self, checked):
        # Toggle Tor connection
        self.privacy_manager.set_tor_enabled(checked)
        
    def toggle_vpn(self, checked):
        # Toggle VPN connection
        self.privacy_manager.set_vpn_enabled(checked)
        
    def show_about(self):
        # Show about dialog
        QMessageBox.about(self, "About", 
            "Securonis Download Manager\n"
            "Version: 0.1.0\n\n"
            "A secure and privacy-focused download manager "
            "developed for a privacy-focused Linux distribution."
        ) 