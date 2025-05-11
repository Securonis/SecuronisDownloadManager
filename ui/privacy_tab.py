#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QCheckBox, QGroupBox, QFormLayout,
                            QLineEdit, QSpinBox, QComboBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot

class PrivacyTab(QWidget):
    def __init__(self, privacy_manager):
        super().__init__()
        
        self.privacy_manager = privacy_manager
        
        # Create UI elements
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Proxy Settings Group
        proxy_group = QGroupBox("Proxy Settings")
        proxy_layout = QVBoxLayout()
        
        # Proxy Type
        proxy_form = QFormLayout()
        
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["None", "HTTP", "SOCKS4", "SOCKS5"])
        self.proxy_type.currentIndexChanged.connect(self.on_proxy_type_changed)
        proxy_form.addRow("Proxy Type:", self.proxy_type)
        
        self.proxy_address = QLineEdit()
        self.proxy_address.setEnabled(False)
        proxy_form.addRow("Proxy Address:", self.proxy_address)
        
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setEnabled(False)
        proxy_form.addRow("Proxy Port:", self.proxy_port)
        
        self.proxy_username = QLineEdit()
        self.proxy_username.setEnabled(False)
        proxy_form.addRow("Username:", self.proxy_username)
        
        self.proxy_password = QLineEdit()
        self.proxy_password.setEnabled(False)
        self.proxy_password.setEchoMode(QLineEdit.Password)
        proxy_form.addRow("Password:", self.proxy_password)
        
        # Proxy Test Button
        self.proxy_test_button = QPushButton("Test Proxy Connection")
        self.proxy_test_button.clicked.connect(self.test_proxy_connection)
        self.proxy_test_button.setEnabled(False)
        proxy_form.addRow("", self.proxy_test_button)
        
        proxy_layout.addLayout(proxy_form)
        proxy_group.setLayout(proxy_layout)
        main_layout.addWidget(proxy_group)
        
        # Leak Prevention Group
        leak_group = QGroupBox("IP/DNS Leak Protection")
        leak_layout = QVBoxLayout()
        
        self.dns_leak_protection = QCheckBox("DNS Leak Protection")
        self.dns_leak_protection.setToolTip("Prevent DNS leaks by using secure DNS servers")
        leak_layout.addWidget(self.dns_leak_protection)
        
        self.webrtc_leak_protection = QCheckBox("WebRTC Leak Protection")
        self.webrtc_leak_protection.setToolTip("Prevent WebRTC from exposing your real IP during downloads")
        leak_layout.addWidget(self.webrtc_leak_protection)
        
        leak_group.setLayout(leak_layout)
        main_layout.addWidget(leak_group)
        
        # Logging Policy Group
        logs_group = QGroupBox("Logging Policy")
        logs_layout = QVBoxLayout()
        
        self.keep_logs = QCheckBox("Keep Download History")
        self.keep_logs.toggled.connect(self.on_keep_logs_toggle)
        logs_layout.addWidget(self.keep_logs)
        
        self.log_retention_days = QSpinBox()
        self.log_retention_days.setRange(1, 365)
        self.log_retention_days.setValue(30)
        self.log_retention_days.setEnabled(False)
        logs_layout.addWidget(QLabel("Keep logs for days:"))
        logs_layout.addWidget(self.log_retention_days)
        
        # Clear Existing Logs
        self.clear_logs_button = QPushButton("Clear All Logs")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        logs_layout.addWidget(self.clear_logs_button)
        
        logs_group.setLayout(logs_layout)
        main_layout.addWidget(logs_group)
        
        # Add stretch
        main_layout.addStretch()
        
        # Apply settings button
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        main_layout.addWidget(self.apply_button)
        
        # Load settings
        self.load_settings()
        
    def load_settings(self):
        # Load settings from privacy_manager
        privacy_settings = self.privacy_manager.get_settings()
        
        # Proxy settings
        proxy_type_index = self.proxy_type.findText(privacy_settings.get('proxy_type', 'None'))
        self.proxy_type.setCurrentIndex(proxy_type_index if proxy_type_index >= 0 else 0)
        self.proxy_address.setText(privacy_settings.get('proxy_address', ''))
        self.proxy_port.setValue(privacy_settings.get('proxy_port', 8080))
        self.proxy_username.setText(privacy_settings.get('proxy_username', ''))
        self.proxy_password.setText(privacy_settings.get('proxy_password', ''))
        
        # Leak prevention settings
        self.dns_leak_protection.setChecked(privacy_settings.get('dns_leak_protection', True))
        self.webrtc_leak_protection.setChecked(privacy_settings.get('webrtc_leak_protection', True))
        
        # Logging policy settings
        self.keep_logs.setChecked(privacy_settings.get('keep_logs', False))
        self.log_retention_days.setValue(privacy_settings.get('log_retention_days', 30))
        self.log_retention_days.setEnabled(self.keep_logs.isChecked())
    
    @pyqtSlot(int)
    def on_proxy_type_changed(self, index):
        # Enable/disable fields based on proxy type
        enabled = index > 0  # 0 = "None"
        self.proxy_address.setEnabled(enabled)
        self.proxy_port.setEnabled(enabled)
        self.proxy_username.setEnabled(enabled)
        self.proxy_password.setEnabled(enabled)
        self.proxy_test_button.setEnabled(enabled)
    
    @pyqtSlot(bool)
    def on_keep_logs_toggle(self, enabled):
        # Enable/disable log retention days field
        self.log_retention_days.setEnabled(enabled)
    
    def test_proxy_connection(self):
        # Test proxy connection
        if self.proxy_type.currentText() == "None":
            return
            
        # Test proxy connection using privacy_manager
        success = self.privacy_manager.test_proxy_connection(
            self.proxy_type.currentText(),
            self.proxy_address.text(),
            self.proxy_port.value(),
            self.proxy_username.text(),
            self.proxy_password.text()
        )
        
        if success:
            QMessageBox.information(self, "Proxy Test", "Proxy connection successful!")
        else:
            QMessageBox.warning(self, "Proxy Test", "Proxy connection failed!")
    
    def clear_logs(self):
        # Clear all logs
        confirm = QMessageBox.question(
            self, 
            "Clear Logs",
            "All download and privacy logs will be deleted. Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.privacy_manager.clear_logs()
            QMessageBox.information(self, "Clear Logs", "All logs have been cleared successfully.")
    
    def apply_settings(self):
        # Apply all settings to privacy_manager
        privacy_settings = {
            # Proxy settings
            'proxy_type': self.proxy_type.currentText(),
            'proxy_address': self.proxy_address.text(),
            'proxy_port': self.proxy_port.value(),
            'proxy_username': self.proxy_username.text(),
            'proxy_password': self.proxy_password.text(),
            
            # Leak prevention settings
            'dns_leak_protection': self.dns_leak_protection.isChecked(),
            'webrtc_leak_protection': self.webrtc_leak_protection.isChecked(),
            
            # Logging policy settings
            'keep_logs': self.keep_logs.isChecked(),
            'log_retention_days': self.log_retention_days.value()
        }
        
        # Save settings
        self.privacy_manager.save_settings(privacy_settings)
        
        # Show success message
        QMessageBox.information(self, "Settings", "Privacy settings saved successfully.") 