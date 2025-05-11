#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QFormLayout, QLabel, QLineEdit, QSpinBox,
                            QCheckBox, QComboBox, QPushButton, QFileDialog,
                            QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSlot

class SettingsTab(QWidget):
    def __init__(self, settings_manager):
        super().__init__()
        
        self.settings_manager = settings_manager
        
        # Create UI elements
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create inner tabs
        self.tab_widget = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        self.setup_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, "General")
        
        # Download settings tab
        download_tab = QWidget()
        self.setup_download_tab(download_tab)
        self.tab_widget.addTab(download_tab, "Download")
        
        # Connection settings tab
        connection_tab = QWidget()
        self.setup_connection_tab(connection_tab)
        self.tab_widget.addTab(connection_tab, "Connection")
        
        # Security settings tab
        security_tab = QWidget()
        self.setup_security_tab(security_tab)
        self.tab_widget.addTab(security_tab, "Security")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button)
        
        # Load settings
        self.load_settings()
        
    def setup_general_tab(self, tab):
        # General settings tab
        layout = QVBoxLayout(tab)
        
        # Startup settings group
        startup_group = QGroupBox("Startup Settings")
        startup_layout = QVBoxLayout()
        
        # Start minimized
        self.start_minimized = QCheckBox("Start minimized in system tray")
        startup_layout.addWidget(self.start_minimized)
        
        # Check for updates on startup
        self.check_updates = QCheckBox("Check for updates on startup")
        startup_layout.addWidget(self.check_updates)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Interface settings group
        ui_group = QGroupBox("Interface Settings")
        ui_layout = QFormLayout()
        
        # Notifications
        self.notifications = QCheckBox("Notify when download completes")
        ui_layout.addRow("", self.notifications)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Download folder group
        folder_group = QGroupBox("Download Folder")
        folder_layout = QHBoxLayout()
        
        self.download_folder = QLineEdit()
        folder_layout.addWidget(self.download_folder)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_download_folder)
        folder_layout.addWidget(self.browse_button)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Add spacing
        layout.addStretch()
        
    def setup_download_tab(self, tab):
        # Download settings tab
        layout = QVBoxLayout(tab)
        
        # Download limits group
        limits_group = QGroupBox("Download Limits")
        limits_layout = QFormLayout()
        
        # Maximum concurrent downloads
        self.max_downloads = QSpinBox()
        self.max_downloads.setRange(1, 20)
        self.max_downloads.setValue(3)
        limits_layout.addRow("Maximum concurrent downloads:", self.max_downloads)
        
        # Download speed limit
        self.speed_limit_enabled = QCheckBox("Enable download speed limit")
        limits_layout.addRow("", self.speed_limit_enabled)
        
        self.speed_limit = QSpinBox()
        self.speed_limit.setRange(10, 100000)
        self.speed_limit.setValue(1000)
        self.speed_limit.setSuffix(" KB/s")
        self.speed_limit.setEnabled(False)
        self.speed_limit_enabled.toggled.connect(self.speed_limit.setEnabled)
        limits_layout.addRow("Speed limit:", self.speed_limit)
        
        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)
        
        # File handling group
        file_group = QGroupBox("File Handling")
        file_layout = QVBoxLayout()
        
        # On download completion
        self.auto_extract = QCheckBox("Automatically extract compressed files")
        file_layout.addWidget(self.auto_extract)
        
        # Hash verification
        self.verify_hash = QCheckBox("Verify file hash when possible")
        file_layout.addWidget(self.verify_hash)
        
        # File name conflict
        self.file_conflict = QComboBox()
        self.file_conflict.addItems([
            "Always ask", 
            "Auto rename", 
            "Overwrite", 
            "Skip download"
        ])
        file_layout.addWidget(QLabel("When file name conflicts:"))
        file_layout.addWidget(self.file_conflict)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Chunked download group
        chunk_group = QGroupBox("Chunked Download")
        chunk_layout = QFormLayout()
        
        # Enable chunked download
        self.chunk_enabled = QCheckBox("Use chunked download")
        self.chunk_enabled.setToolTip("Downloads large files in parallel, increases speed")
        chunk_layout.addRow("", self.chunk_enabled)
        
        # Number of chunks
        self.chunk_count = QSpinBox()
        self.chunk_count.setRange(2, 16)
        self.chunk_count.setValue(4)
        self.chunk_count.setEnabled(False)
        self.chunk_enabled.toggled.connect(self.chunk_count.setEnabled)
        chunk_layout.addRow("Number of chunks:", self.chunk_count)
        
        # Minimum file size
        self.chunk_min_size = QSpinBox()
        self.chunk_min_size.setRange(1, 10000)
        self.chunk_min_size.setValue(10)
        self.chunk_min_size.setSuffix(" MB")
        self.chunk_min_size.setEnabled(False)
        self.chunk_enabled.toggled.connect(self.chunk_min_size.setEnabled)
        chunk_layout.addRow("Minimum file size:", self.chunk_min_size)
        
        chunk_group.setLayout(chunk_layout)
        layout.addWidget(chunk_group)
        
        # Add spacing
        layout.addStretch()
        
    def setup_connection_tab(self, tab):
        # Connection settings tab
        layout = QVBoxLayout(tab)
        
        # Connection timeout group
        timeout_group = QGroupBox("Connection Timeout")
        timeout_layout = QFormLayout()
        
        # Connection timeout
        self.connection_timeout = QSpinBox()
        self.connection_timeout.setRange(5, 300)
        self.connection_timeout.setValue(30)
        self.connection_timeout.setSuffix(" seconds")
        timeout_layout.addRow("Connection timeout:", self.connection_timeout)
        
        # Retry count
        self.retry_count = QSpinBox()
        self.retry_count.setRange(0, 10)
        self.retry_count.setValue(3)
        timeout_layout.addRow("Number of retries:", self.retry_count)
        
        # Retry delay
        self.retry_delay = QSpinBox()
        self.retry_delay.setRange(1, 60)
        self.retry_delay.setValue(5)
        self.retry_delay.setSuffix(" seconds")
        timeout_layout.addRow("Retry delay:", self.retry_delay)
        
        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)
        
        # User agent group
        agent_group = QGroupBox("User Agent")
        agent_layout = QVBoxLayout()
        
        # User agent type
        self.user_agent_type = QComboBox()
        self.user_agent_type.addItems([
            "Browser default", 
            "Chrome", 
            "Firefox", 
            "Safari", 
            "Edge", 
            "Custom"
        ])
        self.user_agent_type.currentIndexChanged.connect(self.on_user_agent_changed)
        agent_layout.addWidget(QLabel("User agent type:"))
        agent_layout.addWidget(self.user_agent_type)
        
        # Custom user agent
        self.custom_user_agent = QLineEdit()
        self.custom_user_agent.setEnabled(False)
        agent_layout.addWidget(QLabel("Custom user agent:"))
        agent_layout.addWidget(self.custom_user_agent)
        
        # Send referer
        self.send_referer = QCheckBox("Send referer information")
        agent_layout.addWidget(self.send_referer)
        
        agent_group.setLayout(agent_layout)
        layout.addWidget(agent_group)
        
        # Add spacing
        layout.addStretch()
        
    def setup_security_tab(self, tab):
        # Security settings tab
        layout = QVBoxLayout(tab)
        
        # Malware scan group
        scan_group = QGroupBox("Malware Scanning")
        scan_layout = QVBoxLayout()
        
        # Scan downloads
        self.scan_downloads = QCheckBox("Scan downloads for malware")
        scan_layout.addWidget(self.scan_downloads)
        
        # Scanner type
        self.scanner_type = QComboBox()
        self.scanner_type.addItems([
            "Built-in", 
            "ClamAV", 
            "Custom"
        ])
        scan_layout.addWidget(QLabel("Scanner type:"))
        scan_layout.addWidget(self.scanner_type)
        
        # Custom scanner command
        self.custom_scanner = QLineEdit()
        scan_layout.addWidget(QLabel("Custom scanner command:"))
        scan_layout.addWidget(self.custom_scanner)
        
        # Malware action
        self.malware_action = QComboBox()
        self.malware_action.addItems([
            "Ask user", 
            "Quarantine", 
            "Delete", 
            "Ignore"
        ])
        scan_layout.addWidget(QLabel("When malware is found:"))
        scan_layout.addWidget(self.malware_action)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # File restrictions group
        restrict_group = QGroupBox("File Restrictions")
        restrict_layout = QVBoxLayout()
        
        # Block dangerous file extensions
        self.block_dangerous = QCheckBox("Block potentially dangerous file extensions (.exe, .bat, etc.)")
        restrict_layout.addWidget(self.block_dangerous)
        
        # Maximum file size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Maximum file size:"))
        
        self.max_file_size_enabled = QCheckBox()
        size_layout.addWidget(self.max_file_size_enabled)
        
        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 100000)
        self.max_file_size.setValue(10000)
        self.max_file_size.setSuffix(" MB")
        self.max_file_size.setEnabled(False)
        self.max_file_size_enabled.toggled.connect(self.max_file_size.setEnabled)
        size_layout.addWidget(self.max_file_size)
        
        size_layout.addStretch()
        restrict_layout.addLayout(size_layout)
        
        restrict_group.setLayout(restrict_layout)
        layout.addWidget(restrict_group)
        
        # Sandbox group
        sandbox_group = QGroupBox("Sandbox")
        sandbox_layout = QVBoxLayout()
        
        # Run download process in sandbox
        self.use_sandbox = QCheckBox("Run download process in sandbox")
        self.use_sandbox.setToolTip("Run download operations in a secure environment")
        sandbox_layout.addWidget(self.use_sandbox)
        
        # Open downloaded applications in sandbox
        self.open_in_sandbox = QCheckBox("Open downloaded applications in sandbox")
        sandbox_layout.addWidget(self.open_in_sandbox)
        
        sandbox_group.setLayout(sandbox_layout)
        layout.addWidget(sandbox_group)
        
        # Add spacing
        layout.addStretch()
        
    def load_settings(self):
        # Load settings from settings_manager
        settings = self.settings_manager.get_all_settings()
        
        # General settings
        self.start_minimized.setChecked(settings.get('start_minimized', False))
        self.check_updates.setChecked(settings.get('check_updates', True))
        
        self.notifications.setChecked(settings.get('notifications', True))
        self.download_folder.setText(settings.get('download_folder', '~/Downloads'))
        
        # Download settings
        self.max_downloads.setValue(settings.get('max_downloads', 3))
        self.speed_limit_enabled.setChecked(settings.get('speed_limit_enabled', False))
        self.speed_limit.setValue(settings.get('speed_limit', 1000))
        self.speed_limit.setEnabled(self.speed_limit_enabled.isChecked())
        
        self.auto_extract.setChecked(settings.get('auto_extract', True))
        self.verify_hash.setChecked(settings.get('verify_hash', True))
        
        conflict_index = self.file_conflict.findText(settings.get('file_conflict', 'Auto rename'))
        self.file_conflict.setCurrentIndex(conflict_index if conflict_index >= 0 else 1)
        
        self.chunk_enabled.setChecked(settings.get('chunk_enabled', True))
        self.chunk_count.setValue(settings.get('chunk_count', 4))
        self.chunk_min_size.setValue(settings.get('chunk_min_size', 10))
        self.chunk_count.setEnabled(self.chunk_enabled.isChecked())
        self.chunk_min_size.setEnabled(self.chunk_enabled.isChecked())
        
        # Connection settings
        self.connection_timeout.setValue(settings.get('connection_timeout', 30))
        self.retry_count.setValue(settings.get('retry_count', 3))
        self.retry_delay.setValue(settings.get('retry_delay', 5))
        
        agent_index = self.user_agent_type.findText(settings.get('user_agent_type', 'Browser default'))
        self.user_agent_type.setCurrentIndex(agent_index if agent_index >= 0 else 0)
        
        self.custom_user_agent.setText(settings.get('custom_user_agent', ''))
        self.custom_user_agent.setEnabled(self.user_agent_type.currentText() == 'Custom')
        
        self.send_referer.setChecked(settings.get('send_referer', True))
        
        # Security settings
        self.scan_downloads.setChecked(settings.get('scan_downloads', True))
        
        scanner_index = self.scanner_type.findText(settings.get('scanner_type', 'Built-in'))
        self.scanner_type.setCurrentIndex(scanner_index if scanner_index >= 0 else 0)
        
        self.custom_scanner.setText(settings.get('custom_scanner', ''))
        
        malware_index = self.malware_action.findText(settings.get('malware_action', 'Ask user'))
        self.malware_action.setCurrentIndex(malware_index if malware_index >= 0 else 0)
        
        self.block_dangerous.setChecked(settings.get('block_dangerous', True))
        self.max_file_size_enabled.setChecked(settings.get('max_file_size_enabled', False))
        self.max_file_size.setValue(settings.get('max_file_size', 10000))
        self.max_file_size.setEnabled(self.max_file_size_enabled.isChecked())
        
        self.use_sandbox.setChecked(settings.get('use_sandbox', False))
        self.open_in_sandbox.setChecked(settings.get('open_in_sandbox', False))
    
    def browse_download_folder(self):
        # Open folder selection dialog
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Download Folder", 
            self.download_folder.text() or "~/"
        )
        
        if folder:
            self.download_folder.setText(folder)
    
    @pyqtSlot(int)
    def on_user_agent_changed(self, index):
        # Enable/disable custom user agent field
        self.custom_user_agent.setEnabled(self.user_agent_type.currentText() == 'Custom')
    
    def save_settings(self):
        # Collect all settings
        general_settings = {
            'start_minimized': self.start_minimized.isChecked(),
            'check_updates': self.check_updates.isChecked(),
            'notifications': self.notifications.isChecked(),
            'download_folder': self.download_folder.text(),
        }
        
        download_settings = {
            'max_downloads': self.max_downloads.value(),
            'speed_limit_enabled': self.speed_limit_enabled.isChecked(),
            'speed_limit': self.speed_limit.value(),
            'auto_extract': self.auto_extract.isChecked(),
            'verify_hash': self.verify_hash.isChecked(),
            'file_conflict': self.file_conflict.currentText(),
            'chunk_enabled': self.chunk_enabled.isChecked(),
            'chunk_count': self.chunk_count.value(),
            'chunk_min_size': self.chunk_min_size.value(),
        }
        
        connection_settings = {
            'connection_timeout': self.connection_timeout.value(),
            'retry_count': self.retry_count.value(),
            'retry_delay': self.retry_delay.value(),
            'user_agent_type': self.user_agent_type.currentText(),
            'custom_user_agent': self.custom_user_agent.text(),
            'send_referer': self.send_referer.isChecked(),
        }
        
        security_settings = {
            'scan_downloads': self.scan_downloads.isChecked(),
            'scanner_type': self.scanner_type.currentText(),
            'custom_scanner': self.custom_scanner.text(),
            'malware_action': self.malware_action.currentText(),
            'block_dangerous': self.block_dangerous.isChecked(),
            'max_file_size_enabled': self.max_file_size_enabled.isChecked(),
            'max_file_size': self.max_file_size.value(),
            'use_sandbox': self.use_sandbox.isChecked(),
            'open_in_sandbox': self.open_in_sandbox.isChecked()
        }
        
        # Save each section separately
        self.settings_manager.save_section('general', general_settings)
        self.settings_manager.save_section('download', download_settings)
        self.settings_manager.save_section('connection', connection_settings)
        self.settings_manager.save_section('security', security_settings)
        
        # Show success message
        QMessageBox.information(self, "Settings", "Settings saved successfully.") 