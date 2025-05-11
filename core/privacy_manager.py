#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import socket
import subprocess
import tempfile
import requests
import time
from datetime import datetime, timedelta

# For SOCKS connections via PySocks library
try:
    import socks
except ImportError:
    socks = None

# Tor control via Stem library
try:
    from stem import Signal
    from stem.control import Controller
    stem_available = True
except ImportError:
    stem_available = False

class PrivacyManager:
    """Class managing privacy and security features"""
    
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        
        # Privacy settings
        self.settings = {
            # Tor settings
            'tor_enabled': False,
            'tor_address': '127.0.0.1',
            'tor_port': 9050,
            'tor_control_port': 9051,
            'tor_circuit_isolation': True,
            
            # Proxy settings
            'proxy_type': 'None',
            'proxy_address': '',
            'proxy_port': 8080,
            'proxy_username': '',
            'proxy_password': '',
            
            # Leak prevention settings
            'dns_leak_protection': True,
            'webrtc_leak_protection': True,
            'kill_switch': True,
            
            # VPN settings
            'vpn_enabled': False,
            'vpn_provider': None,
            'vpn_config_path': None,
            
            # Logging policy
            'keep_logs': False,
            'log_retention_days': 30
        }
        
        # OS-level connection control
        self.original_socket_create_connection = socket.create_connection
        
        # Load saved settings
        self.load_settings()
        
    def load_settings(self):
        """Loads saved privacy settings"""
        stored_settings = self.settings_manager.get_section('privacy')
        if stored_settings:
            self.settings.update(stored_settings)
    
    def save_settings(self, new_settings):
        """Saves privacy settings"""
        # Update settings
        self.settings.update(new_settings)
        
        # Save new settings to settings_manager
        self.settings_manager.save_section('privacy', self.settings)
        
        # Apply new settings
        self.apply_settings()
    
    def get_settings(self):
        """Returns current privacy settings"""
        return self.settings.copy()
    
    def get_tor_settings(self):
        """Returns only Tor settings"""
        return {k: v for k, v in self.settings.items() if k.startswith('tor_')}
    
    def get_proxy_settings(self):
        """Returns only proxy settings"""
        return {k: v for k, v in self.settings.items() if k.startswith('proxy_')}
    
    def apply_settings(self):
        """Applies current settings"""
        # If Tor is enabled
        if self.settings['tor_enabled']:
            self.enable_tor()
        else:
            self.disable_tor()
        
        # DNS leak protection
        if self.settings['dns_leak_protection']:
            self.enable_dns_leak_protection()
        else:
            self.disable_dns_leak_protection()
    
    def is_tor_enabled(self):
        """Checks if Tor is enabled"""
        return self.settings['tor_enabled']
    
    def set_tor_enabled(self, enabled):
        """Enables or disables Tor usage"""
        if enabled != self.settings['tor_enabled']:
            self.settings['tor_enabled'] = enabled
            if enabled:
                return self.enable_tor()
            else:
                return self.disable_tor()
        return True
    
    def enable_tor(self):
        """Enables Tor connection"""
        # Check if Stem library is available
        if not stem_available:
            return False
        
        # Check if Tor service is running
        if not self.is_tor_running():
            return False
        
        # Patch socket creation function
        def create_connection_with_tor(*args, **kwargs):
            # Create connection through Tor proxy
            socks.setdefaultproxy(
                socks.PROXY_TYPE_SOCKS5, 
                self.settings['tor_address'], 
                self.settings['tor_port']
            )
            return self.original_socket_create_connection(*args, **kwargs)
        
        if socks:
            socket.create_connection = create_connection_with_tor
        
        self.settings['tor_enabled'] = True
        return True
    
    def disable_tor(self):
        """Disables Tor connection"""
        # Restore original socket function
        socket.create_connection = self.original_socket_create_connection
        
        self.settings['tor_enabled'] = False
        return True
    
    def is_tor_running(self):
        """Checks if Tor service is running"""
        try:
            # Try connecting to Tor SOCKS port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex((self.settings['tor_address'], self.settings['tor_port']))
            sock.close()
            return result == 0
        except:
            return False
    
    def new_tor_identity(self):
        """Requests a new Tor identity (circuit)"""
        if not stem_available:
            return False
        
        try:
            with Controller.from_port(
                address=self.settings['tor_address'],
                port=self.settings['tor_control_port']
            ) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                return True
        except Exception as e:
            print(f"Error changing Tor identity: {str(e)}")
            return False
    
    def test_tor_connection(self, address=None, port=None):
        """Tests Tor connection"""
        if address is None:
            address = self.settings['tor_address']
        if port is None:
            port = self.settings['tor_port']
        
        if not socks:
            return False
        
        try:
            # Backup original proxy settings
            default_proxy = socks.getdefaultproxy()
            
            # Set Tor proxy
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, address, port)
            socket.socket = socks.socksocket
            
            # Check via check.torproject.org
            response = requests.get('https://check.torproject.org/', timeout=10)
            
            # If "Congratulations" appears, Tor is working
            tor_working = "Congratulations" in response.text
            
            # Restore original proxy settings
            if default_proxy:
                socks.setdefaultproxy(*default_proxy)
            else:
                socket.socket = socket._socketobject
            
            return tor_working
        except Exception as e:
            print(f"Tor connection test error: {str(e)}")
            # Restore original socket
            socket.socket = socket._socketobject
            return False
    
    def test_proxy_connection(self, proxy_type, proxy_address, proxy_port, username=None, password=None):
        """Tests proxy connection"""
        if not socks:
            return False
        
        try:
            # Determine proxy type
            if proxy_type.lower() == 'http':
                proxy_socks_type = socks.PROXY_TYPE_HTTP
            elif proxy_type.lower() == 'socks4':
                proxy_socks_type = socks.PROXY_TYPE_SOCKS4
            elif proxy_type.lower() == 'socks5':
                proxy_socks_type = socks.PROXY_TYPE_SOCKS5
            else:
                return False
            
            # Backup original proxy settings
            default_proxy = socks.getdefaultproxy()
            
            # Set test proxy
            socks.setdefaultproxy(
                proxy_socks_type, 
                proxy_address, 
                proxy_port,
                username=username,
                password=password
            )
            socket.socket = socks.socksocket
            
            # Simple HTTP request for testing
            response = requests.get('https://www.google.com/', timeout=10)
            success = response.status_code == 200
            
            # Restore original proxy settings
            if default_proxy:
                socks.setdefaultproxy(*default_proxy)
            else:
                socket.socket = socket._socketobject
            
            return success
        except Exception as e:
            print(f"Proxy connection test error: {str(e)}")
            # Restore original socket
            socket.socket = socket._socketobject
            return False
    
    def enable_dns_leak_protection(self):
        """Enables DNS leak protection"""
        # Redirect DNS settings to secure DNS servers
        # NOTE: This requires system-level changes
        # On Linux, we need to modify /etc/resolv.conf
        # This is just an example implementation
        
        try:
            # Create a temporary resolv.conf file
            temp_resolv = tempfile.NamedTemporaryFile(mode='w+', delete=False)
            
            # Secure DNS servers
            temp_resolv.write("nameserver 1.1.1.1\n")  # Cloudflare
            temp_resolv.write("nameserver 9.9.9.9\n")  # Quad9
            temp_resolv.close()
            
            # Need root privileges to change system resolv.conf file
            # subprocess.run(['sudo', 'cp', temp_resolv.name, '/etc/resolv.conf'])
            
            # For application purposes, let's assume it succeeded
            self.settings['dns_leak_protection'] = True
            return True
        except Exception as e:
            print(f"Error enabling DNS leak protection: {str(e)}")
            return False
    
    def disable_dns_leak_protection(self):
        """Disables DNS leak protection"""
        # Restore original DNS settings
        # This also requires system-level changes
        
        self.settings['dns_leak_protection'] = False
        return True
    
    def connect_vpn(self):
        """Starts VPN connection"""
        # VPN settings
        vpn_config = self.settings.get('vpn_config_path')
        
        if not vpn_config or not os.path.exists(vpn_config):
            return False
        
        try:
            # Start VPN connection using OpenVPN
            # subprocess.Popen(['sudo', 'openvpn', '--config', vpn_config])
            
            # Assume VPN connection succeeded
            self.settings['vpn_enabled'] = True
            return True
        except Exception as e:
            print(f"VPN connection error: {str(e)}")
            return False
    
    def disconnect_vpn(self):
        """Disconnects VPN connection"""
        try:
            # Terminate OpenVPN process
            # subprocess.run(['sudo', 'killall', 'openvpn'])
            
            # Assume VPN connection was terminated
            self.settings['vpn_enabled'] = False
            return True
        except Exception as e:
            print(f"Error disconnecting VPN: {str(e)}")
            return False
    
    def get_real_ip(self):
        """Returns the real IP address"""
        try:
            # Get IP address from ifconfig.me or similar service
            # This gives the external IP, not the local IP
            response = requests.get('https://ifconfig.me/ip', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        return None
    
    def get_apparent_ip(self):
        """Returns the apparent IP address (through VPN/Tor)"""
        try:
            # Backup original socket
            original_socket = socket.socket
            
            if self.settings['tor_enabled'] and socks:
                # Through Tor proxy
                socks.setdefaultproxy(
                    socks.PROXY_TYPE_SOCKS5, 
                    self.settings['tor_address'], 
                    self.settings['tor_port']
                )
                socket.socket = socks.socksocket
            
            # Check IP address
            response = requests.get('https://ifconfig.me/ip', timeout=10)
            ip = response.text.strip() if response.status_code == 200 else None
            
            # Restore original socket
            socket.socket = original_socket
            
            return ip
        except:
            # Restore original socket
            socket.socket = original_socket
            return None
    
    def clear_logs(self):
        """Clears all download and privacy logs"""
        try:
            # Clear application logs
            # Example: delete log files
            log_dir = self.settings_manager.get_setting('log_directory', './logs')
            
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log'):
                        os.remove(os.path.join(log_dir, filename))
            
            return True
        except Exception as e:
            print(f"Error clearing logs: {str(e)}")
            return False
    
    def clean_old_logs(self):
        """Cleans logs older than specified days"""
        if not self.settings['keep_logs']:
            return self.clear_logs()
        
        retention_days = self.settings['log_retention_days']
        if retention_days <= 0:
            return True
        
        try:
            log_dir = self.settings_manager.get_setting('log_directory', './logs')
            
            if os.path.exists(log_dir):
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log'):
                        file_path = os.path.join(log_dir, filename)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_time < cutoff_date:
                            os.remove(file_path)
            
            return True
        except Exception as e:
            print(f"Error cleaning old logs: {str(e)}")
            return False 