#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QStatusBar
from PyQt5.QtCore import QSettings

# Import other modules to keep the project modular
from ui.main_window import MainWindow
from core.download_manager import DownloadManager
from core.privacy_manager import PrivacyManager
from core.settings_manager import SettingsManager

def main():
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Securonis Download Manager")
    app.setOrganizationName("Securonis")
    
    # Initialize main components
    settings = SettingsManager()
    privacy_manager = PrivacyManager(settings)
    download_manager = DownloadManager(settings, privacy_manager)
    
    # Create main window
    main_window = MainWindow(download_manager, privacy_manager, settings)
    main_window.show()
    
    # Start application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 