#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import uuid
import threading
import queue
import requests
import tempfile
import shutil
import hashlib
from urllib.parse import urlparse, unquote
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class Download:
    """Class representing a download task"""
    
    def __init__(self, url, target_dir, filename=None):
        self.id = str(uuid.uuid4())
        self.url = url
        self.target_dir = target_dir
        self.filename = filename or self._extract_filename(url)
        
        self.size = -1
        self.downloaded = 0
        self.progress = 0
        self.speed = 0
        self.start_time = 0
        self.eta = -1
        self.status = "Waiting"
        self.error = None
        self.privacy_mode = "Normal"
        
        # For chunked downloads
        self.chunks = []
        self.chunk_status = {}
    
    def _extract_filename(self, url):
        """Extracts filename from URL"""
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        return os.path.basename(path) or "download"
    
    def get_target_path(self):
        """Returns the full target path for this download"""
        return os.path.join(self.target_dir, self.filename)
    
    def calculate_progress(self):
        """Calculates download progress percentage"""
        if self.size > 0:
            self.progress = int((self.downloaded / self.size) * 100)
        else:
            self.progress = 0
    
    def calculate_speed(self, elapsed_time):
        """Calculates download speed in bytes per second"""
        if elapsed_time > 0:
            self.speed = self.downloaded / elapsed_time
            
            # Calculate estimated time of arrival (ETA)
            if self.speed > 0 and self.size > 0:
                remaining_bytes = self.size - self.downloaded
                self.eta = remaining_bytes / self.speed
            else:
                self.eta = -1
        else:
            self.speed = 0
            self.eta = -1

class DownloadManager(QObject):
    """Class managing download operations"""
    
    # Signals
    download_added = pyqtSignal(str)  # download_id
    download_started = pyqtSignal(str)  # download_id
    download_completed = pyqtSignal(str)  # download_id
    download_failed = pyqtSignal(str, str)  # download_id, error_message
    download_paused = pyqtSignal(str)  # download_id
    download_resumed = pyqtSignal(str)  # download_id
    download_canceled = pyqtSignal(str)  # download_id
    download_progress = pyqtSignal(str, int, int)  # download_id, downloaded_bytes, total_bytes
    
    def __init__(self, settings_manager, privacy_manager):
        super().__init__()
        
        self.settings_manager = settings_manager
        self.privacy_manager = privacy_manager
        
        # Download settings
        self.max_downloads = settings_manager.get_setting('max_downloads', 3)
        self.speed_limit = settings_manager.get_setting('speed_limit', 0)
        self.chunk_enabled = settings_manager.get_setting('chunk_enabled', True)
        self.chunk_count = settings_manager.get_setting('chunk_count', 4)
        self.chunk_min_size = settings_manager.get_setting('chunk_min_size', 10) * 1024 * 1024  # Convert MB to bytes
        self.auto_extract = settings_manager.get_setting('auto_extract', True)
        self.verify_hash = settings_manager.get_setting('verify_hash', True)
        self.file_conflict = settings_manager.get_setting('file_conflict', 'Auto rename')
        self.connection_timeout = settings_manager.get_setting('connection_timeout', 30)
        self.retry_count = settings_manager.get_setting('retry_count', 3)
        self.retry_delay = settings_manager.get_setting('retry_delay', 5)
        
        # Active downloads
        self.downloads = {}
        self.downloads_lock = threading.RLock()
        
        # Download queue and workers
        self.download_queue = queue.Queue()
        self.active_workers = 0
        self.max_workers = self.max_downloads
        self.workers = []
        
        # Start workers
        self._start_workers()
    
    def _start_workers(self):
        """Starts download worker threads"""
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._download_worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def add_download(self, url, target_dir, filename=None, privacy_mode="Normal"):
        """Adds a new download to the queue"""
        download = Download(url, target_dir, filename)
        download.privacy_mode = privacy_mode
        download.status = "Waiting"
        
        with self.downloads_lock:
            self.downloads[download.id] = download
        
        self.download_queue.put(download.id)
        self.download_added.emit(download.id)
        
        return download.id
    
    def pause_download(self, download_id):
        """Pauses a download"""
        with self.downloads_lock:
            if download_id in self.downloads:
                download = self.downloads[download_id]
                if download.status == "Downloading":
                    download.status = "Paused"
                    self.download_paused.emit(download_id)
                    return True
        return False
    
    def resume_download(self, download_id):
        """Resumes a paused download"""
        with self.downloads_lock:
            if download_id in self.downloads:
                download = self.downloads[download_id]
                if download.status == "Paused":
                    download.status = "Waiting"
                    self.download_queue.put(download_id)
                    self.download_resumed.emit(download_id)
                    return True
        return False
    
    def cancel_download(self, download_id):
        """Cancels a download"""
        with self.downloads_lock:
            if download_id in self.downloads:
                download = self.downloads[download_id]
                if download.status in ["Downloading", "Paused", "Waiting"]:
                    download.status = "Canceled"
                    self.download_canceled.emit(download_id)
                    return True
        return False
    
    def delete_download(self, download_id):
        """Deletes a download from the list"""
        with self.downloads_lock:
            if download_id in self.downloads:
                download = self.downloads[download_id]
                
                # Cancel if active
                if download.status in ["Downloading", "Waiting"]:
                    self.cancel_download(download_id)
                
                # Delete from list
                del self.downloads[download_id]
                return True
        return False
    
    def stop_download(self, download_id):
        """Stops a download (same as pause)"""
        return self.pause_download(download_id)
    
    def clear_completed(self):
        """Clears completed downloads from the list"""
        with self.downloads_lock:
            completed_ids = [d_id for d_id, d in self.downloads.items() 
                            if d.status == "Completed"]
            
            for download_id in completed_ids:
                del self.downloads[download_id]
    
    def get_download(self, download_id):
        """Returns a specific download"""
        with self.downloads_lock:
            return self.downloads.get(download_id)
    
    def get_default_save_path(self):
        """Returns the default download directory"""
        # Get from settings or use ~/Downloads as fallback
        download_folder = self.settings_manager.get_setting('download_folder', os.path.expanduser('~/Downloads'))
        
        # Create the directory if it doesn't exist
        os.makedirs(download_folder, exist_ok=True)
        
        return download_folder
    
    def get_all_downloads(self):
        """Lists all downloads"""
        with self.downloads_lock:
            return list(self.downloads.values())
    
    def _download_worker(self):
        """Background thread to process download operations"""
        while True:
            try:
                # Get next download ID from queue
                download_id = self.download_queue.get()
                
                with self.downloads_lock:
                    if download_id not in self.downloads:
                        self.download_queue.task_done()
                        continue
                    
                    download = self.downloads[download_id]
                    
                    # Skip if download is canceled or completed
                    if download.status in ["Canceled", "Completed", "Failed"]:
                        self.download_queue.task_done()
                        continue
                    
                    # Mark as downloading
                    download.status = "Downloading"
                    self.active_workers += 1
                
                self.download_started.emit(download_id)
                
                # Perform the download
                try:
                    success = self._download_file(download_id)
                    
                    with self.downloads_lock:
                        if download_id in self.downloads:
                            if success:
                                self.downloads[download_id].status = "Completed"
                                self.download_completed.emit(download_id)
                            else:
                                # If paused/canceled, don't change status to failed
                                if self.downloads[download_id].status == "Downloading":
                                    self.downloads[download_id].status = "Failed"
                                    self.download_failed.emit(download_id, self.downloads[download_id].error or "Unknown error")
                except Exception as e:
                    with self.downloads_lock:
                        if download_id in self.downloads:
                            self.downloads[download_id].status = "Failed"
                            self.downloads[download_id].error = str(e)
                            self.download_failed.emit(download_id, str(e))
                
                with self.downloads_lock:
                    self.active_workers -= 1
                
                self.download_queue.task_done()
            except Exception as e:
                print(f"Error in download worker: {str(e)}")
    
    def _download_file(self, download_id):
        """Downloads a specific file"""
        try:
            with self.downloads_lock:
                if download_id not in self.downloads:
                    return
                download = self.downloads[download_id]
            
            # Download start time
            download.start_time = time.time()
            
            # Proxy and Tor settings
            proxies = self._get_proxies(download.privacy_mode)
            
            # HTTP Headers
            headers = self._get_headers()
            
            # HEAD request for file information
            head_response = requests.head(
                download.url, 
                headers=headers,
                proxies=proxies,
                timeout=self.connection_timeout,
                allow_redirects=True
            )
            
            # File size
            content_length = head_response.headers.get('content-length')
            if content_length and content_length.isdigit():
                download.size = int(content_length)
            
            # Get real filename (if provided by server)
            content_disposition = head_response.headers.get('content-disposition')
            if content_disposition:
                import re
                filename_match = re.search(r'filename="?([^";]+)', content_disposition)
                if filename_match:
                    download.filename = filename_match.group(1)
            
            # Check download URL (if redirected)
            download.url = head_response.url
            
            # Target file path
            target_path = download.get_target_path()
            
            # Check if supports range requests
            supports_range = 'accept-ranges' in head_response.headers and head_response.headers['accept-ranges'] == 'bytes'
            
            # Use chunked download if supported and enabled
            if supports_range and self.chunk_enabled and download.size >= self.chunk_min_size:
                return self._download_in_chunks(download, proxies, headers)
            else:
                return self._download_single(download, proxies, headers)
        except Exception as e:
            with self.downloads_lock:
                if download_id in self.downloads:
                    self.downloads[download_id].error = str(e)
            print(f"Error downloading file: {str(e)}")
            return False
    
    def _download_single(self, download, proxies, headers):
        """Single connection download strategy"""
        target_path = download.get_target_path()
        temp_path = target_path + ".part"
        
        # Check if file exists
        if os.path.exists(target_path):
            # Handle file conflicts based on settings
            if self.file_conflict == "Skip download":
                return True
            elif self.file_conflict == "Overwrite":
                pass  # Just overwrite
            elif self.file_conflict == "Auto rename":
                base, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(target_path):
                    target_path = f"{base} ({counter}){ext}"
                    counter += 1
                download.filename = os.path.basename(target_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Try to download with retries
        retries = 0
        while retries <= self.retry_count:
            try:
                with requests.get(
                    download.url, 
                    headers=headers,
                    proxies=proxies,
                    stream=True,
                    timeout=self.connection_timeout
                ) as response:
                    response.raise_for_status()
                    
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            # Check if download is paused or canceled
                            if download.status != "Downloading":
                                return False
                            
                            if chunk:
                                f.write(chunk)
                                download.downloaded += len(chunk)
                                download.calculate_progress()
                                
                                # Calculate speed
                                elapsed = time.time() - download.start_time
                                download.calculate_speed(elapsed)
                                
                                # Send progress signal
                                self.download_progress.emit(download.id, download.downloaded, download.size)
                
                # Download completed, move temp file to target
                shutil.move(temp_path, target_path)
                
                # Post-processing
                self._post_process_download(download, target_path)
                
                return True
            except Exception as e:
                retries += 1
                if retries > self.retry_count:
                    download.error = str(e)
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return False
                
                # Wait before retry
                time.sleep(self.retry_delay)
        
        return False
    
    def _download_in_chunks(self, download, proxies, headers):
        """Chunked download strategy"""
        target_path = download.get_target_path()
        
        # Check if file exists and handle conflicts
        if os.path.exists(target_path):
            # Handle file conflicts based on settings
            if self.file_conflict == "Skip download":
                return True
            elif self.file_conflict == "Overwrite":
                pass  # Just overwrite
            elif self.file_conflict == "Auto rename":
                base, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(target_path):
                    target_path = f"{base} ({counter}){ext}"
                    counter += 1
                download.filename = os.path.basename(target_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Prepare chunks
        chunk_size = download.size // self.chunk_count
        chunks = []
        
        for i in range(self.chunk_count):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < self.chunk_count - 1 else download.size - 1
            
            temp_file = f"{target_path}.part{i}"
            chunks.append({
                'start': start,
                'end': end,
                'temp_file': temp_file,
                'downloaded': 0,
                'status': 'waiting'
            })
        
        download.chunks = chunks
        
        # Create threads for each chunk
        chunk_threads = []
        for i, chunk in enumerate(chunks):
            thread = threading.Thread(
                target=self._download_chunk, 
                args=(download, chunk, proxies, headers.copy())
            )
            thread.daemon = True
            thread.start()
            chunk_threads.append(thread)
        
        # Wait for all chunks to complete
        for thread in chunk_threads:
            thread.join()
        
        # Check if all chunks completed successfully
        if all(chunk['status'] == 'completed' for chunk in chunks):
            # Combine chunks
            with open(target_path, 'wb') as output:
                for chunk in chunks:
                    with open(chunk['temp_file'], 'rb') as input:
                        shutil.copyfileobj(input, output)
            
            # Clean up temp files
            for chunk in chunks:
                if os.path.exists(chunk['temp_file']):
                    os.remove(chunk['temp_file'])
            
            # Post-processing
            self._post_process_download(download, target_path)
            
            return True
        else:
            # Download failed
            download.error = "Some chunks failed to download"
            
            # Clean up temp files
            for chunk in chunks:
                if os.path.exists(chunk['temp_file']):
                    os.remove(chunk['temp_file'])
            
            return False
    
    def _download_chunk(self, download, chunk, proxies, headers):
        """Downloads a single chunk of a file"""
        retries = 0
        while retries <= self.retry_count:
            try:
                # Add range header for this chunk
                headers['Range'] = f"bytes={chunk['start']}-{chunk['end']}"
                
                chunk['status'] = 'downloading'
                
                with requests.get(
                    download.url, 
                    headers=headers,
                    proxies=proxies,
                    stream=True,
                    timeout=self.connection_timeout
                ) as response:
                    response.raise_for_status()
                    
                    with open(chunk['temp_file'], 'wb') as f:
                        for data in response.iter_content(chunk_size=8192):
                            # Check if download is paused or canceled
                            if download.status != "Downloading":
                                return
                            
                            if data:
                                f.write(data)
                                chunk['downloaded'] += len(data)
                                
                                # Update total downloaded amount
                                with self.downloads_lock:
                                    download.downloaded = sum(c['downloaded'] for c in download.chunks)
                                    download.calculate_progress()
                                    
                                    # Calculate speed
                                    elapsed = time.time() - download.start_time
                                    download.calculate_speed(elapsed)
                                
                                # Send progress signal
                                self.download_progress.emit(download.id, download.downloaded, download.size)
                
                # Chunk successfully downloaded
                chunk['status'] = 'completed'
                return
                
            except Exception as e:
                retries += 1
                if retries > self.retry_count:
                    chunk['status'] = 'failed'
                    chunk['error'] = str(e)
                    raise
                
                # Wait before retry
                time.sleep(self.retry_delay)
    
    def _post_process_download(self, download, file_path):
        """Performs post-processing on downloaded file"""
        # Verify hash if available and enabled
        if self.verify_hash and hasattr(download, 'expected_hash'):
            self._verify_file_hash(file_path, download.expected_hash)
        
        # Auto-extract archives
        if self.auto_extract and self._is_archive(file_path):
            self._extract_archive(file_path, os.path.dirname(file_path))
    
    def _verify_file_hash(self, file_path, expected_hash):
        """Verifies file integrity using hash"""
        # This should verify different hash types (MD5, SHA1, SHA256)
        # Implementation not complete
        pass
    
    def _is_archive(self, file_path):
        """Checks if file is an archive that can be extracted"""
        # Simple check based on extension
        extensions = ['.zip', '.rar', '.tar', '.gz', '.7z']
        return any(file_path.lower().endswith(ext) for ext in extensions)
    
    def _extract_archive(self, archive_path, target_dir):
        """Extracts an archive file"""
        # This would use appropriate extraction tools based on archive type
        # Implementation not complete
        pass
    
    def _get_proxies(self, privacy_mode):
        """Configures proxies based on privacy mode"""
        proxies = {}
        
        if privacy_mode == "Tor" and self.privacy_manager.is_tor_enabled():
            # Configure for Tor
            tor_address = self.privacy_manager.settings.get('tor_address', '127.0.0.1')
            tor_port = self.privacy_manager.settings.get('tor_port', 9050)
            proxies = {
                'http': f'socks5://{tor_address}:{tor_port}',
                'https': f'socks5://{tor_address}:{tor_port}'
            }
        elif privacy_mode == "Proxy":
            # Configure custom proxy
            proxy_settings = self.privacy_manager.get_proxy_settings()
            if proxy_settings['proxy_type'] != 'None':
                proxy_type = proxy_settings['proxy_type'].lower()
                proxy_address = proxy_settings['proxy_address']
                proxy_port = proxy_settings['proxy_port']
                
                auth = ""
                if proxy_settings['proxy_username'] and proxy_settings['proxy_password']:
                    auth = f"{proxy_settings['proxy_username']}:{proxy_settings['proxy_password']}@"
                
                proxies = {
                    'http': f'{proxy_type}://{auth}{proxy_address}:{proxy_port}',
                    'https': f'{proxy_type}://{auth}{proxy_address}:{proxy_port}'
                }
        
        return proxies
    
    def _get_headers(self):
        """Creates HTTP headers for the download request"""
        headers = {}
        
        # User agent
        user_agent_type = self.settings_manager.get_setting('user_agent_type', 'Browser default')
        
        if user_agent_type == 'Custom':
            headers['User-Agent'] = self.settings_manager.get_setting('custom_user_agent', '')
        elif user_agent_type == 'Browser default':
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # Referer
        send_referer = self.settings_manager.get_setting('send_referer', True)
        if not send_referer:
            headers['Referer'] = ''
        
        return headers 