#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal

class SettingsManager(QObject):
    """Class managing application settings"""
    
    # Send signal when settings change
    settings_changed = pyqtSignal(str)  # section_name
    
    def __init__(self, config_file=None):
        super().__init__()
        
        # Default settings
        self.settings = {
            'general': {
                'startup_enabled': False,
                'start_minimized': False,
                'check_updates': True,
                'language': 'English',
                'theme': 'System',
                'notifications': True,
                'download_folder': os.path.expanduser('~/Downloads')
            },
            'download': {
                'max_downloads': 3,
                'speed_limit_enabled': False,
                'speed_limit': 1000,
                'auto_extract': True,
                'verify_hash': True,
                'file_conflict': 'Auto rename',
                'chunk_enabled': True,
                'chunk_count': 4,
                'chunk_min_size': 10
            },
            'connection': {
                'connection_timeout': 30,
                'retry_count': 3,
                'retry_delay': 5,
                'user_agent_type': 'Browser default',
                'custom_user_agent': '',
                'send_referer': True
            },
            'security': {
                'scan_downloads': False,
                'scanner_type': 'Built-in',
                'custom_scanner': '',
                'malware_action': 'Ask user',
                'block_dangerous': True,
                'max_file_size_enabled': False,
                'max_file_size': 10000,
                'use_sandbox': False,
                'open_in_sandbox': False
            },
            'privacy': {}  # To be filled by Privacy Manager
        }
        
        # Configuration file path
        if config_file is None:
            # Default configuration file
            config_dir = os.path.expanduser('~/.config/securonis/')
            os.makedirs(config_dir, exist_ok=True)
            self.config_file = os.path.join(config_dir, 'settings.json')
        else:
            self.config_file = config_file
        
        # Load configuration file
        self.load_settings()
        
        # Auto-save timer
        self.auto_save_timer = None
        self.pending_save = False
    
    def load_settings(self):
        """Loads settings from configuration file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                    # Update each section
                    for section, values in loaded_settings.items():
                        if section in self.settings:
                            self.settings[section].update(values)
                        else:
                            self.settings[section] = values
            except Exception as e:
                print(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Saves all settings to configuration file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            self.pending_save = False
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
    
    def schedule_save(self, delay=2.0):
        """Schedules settings to be saved after specified delay"""
        self.pending_save = True
        
        # Cancel existing timer
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        # Create new timer
        self.auto_save_timer = threading.Timer(delay, self.save_settings)
        self.auto_save_timer.daemon = True
        self.auto_save_timer.start()
    
    def get_all_settings(self):
        """Returns all settings as a flattened dictionary"""
        # Combine settings from all sections
        all_settings = {}
        for section_values in self.settings.values():
            all_settings.update(section_values)
        return all_settings
    
    def get_section(self, section):
        """Returns all settings from a specific section"""
        return self.settings.get(section, {}).copy()
    
    def get_setting(self, key, default=None):
        """Gets a specific setting by name"""
        # Search in all sections
        for section_values in self.settings.values():
            if key in section_values:
                return section_values[key]
        return default
    
    def set_setting(self, key, value, section=None):
        """Sets a specific setting"""
        # If section is specified, update directly
        if section is not None:
            if section in self.settings:
                self.settings[section][key] = value
                self.settings_changed.emit(section)
                self.schedule_save()
                return True
            return False
        
        # Otherwise search in all sections
        for section_name, section_values in self.settings.items():
            if key in section_values:
                section_values[key] = value
                self.settings_changed.emit(section_name)
                self.schedule_save()
                return True
        
        # Key not found in any section
        return False
    
    def save_section(self, section, values):
        """Updates and saves a complete section"""
        if section in self.settings:
            self.settings[section].update(values)
        else:
            self.settings[section] = values
        
        self.settings_changed.emit(section)
        self.schedule_save()
        return True
    
    def reset_section(self, section):
        """Resets a section to default settings"""
        if section in self.settings:
            from copy import deepcopy
            
            # Find original default section
            defaults = {
                'general': {
                    'startup_enabled': False,
                    'start_minimized': False,
                    'check_updates': True,
                    'language': 'English',
                    'theme': 'System',
                    'notifications': True,
                    'download_folder': os.path.expanduser('~/Downloads')
                },
                'download': {
                    'max_downloads': 3,
                    'speed_limit_enabled': False,
                    'speed_limit': 1000,
                    'auto_extract': True,
                    'verify_hash': True,
                    'file_conflict': 'Auto rename',
                    'chunk_enabled': True,
                    'chunk_count': 4,
                    'chunk_min_size': 10
                },
                'connection': {
                    'connection_timeout': 30,
                    'retry_count': 3,
                    'retry_delay': 5,
                    'user_agent_type': 'Browser default',
                    'custom_user_agent': '',
                    'send_referer': True
                },
                'security': {
                    'scan_downloads': False,
                    'scanner_type': 'Built-in',
                    'custom_scanner': '',
                    'malware_action': 'Ask user',
                    'block_dangerous': True,
                    'max_file_size_enabled': False,
                    'max_file_size': 10000,
                    'use_sandbox': False,
                    'open_in_sandbox': False
                },
                'privacy': {}  # Default settings for Privacy Manager
            }
            
            # Reset if default exists
            if section in defaults:
                self.settings[section] = deepcopy(defaults[section])
                self.settings_changed.emit(section)
                self.schedule_save()
                return True
        
        return False
    
    def reset_all_settings(self):
        """Resets all settings to default values"""
        # Reset each section
        for section in list(self.settings.keys()):
            self.reset_section(section)
        
        self.schedule_save()
        return True
    
    def test_connection(self, callback):
        """Tests connection speed"""
        def run_test():
            # Speedtest library can be used for speed test
            # This example uses manual simulation
            try:
                time.sleep(2)  # Test simulation
                
                # Example speed values
                download_speed = 10.5  # Mbps
                upload_speed = 5.2  # Mbps
                
                # Pass results to callback function
                callback(download_speed, upload_speed)
            except Exception as e:
                print(f"Connection test error: {str(e)}")
                callback(0, 0)
        
        # Run speed test in a separate thread
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
    
    def __del__(self):
        """Destructor method: cancel timer and save pending records"""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        if self.pending_save:
            self.save_settings() 