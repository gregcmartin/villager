# -*- coding: utf-8 -*-
import uuid
import json
import asyncio
import threading
from pathlib import Path
from typing import Union, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import queue
import atexit


@dataclass
class ShareGPTLoggerConfig:
    """ShareGPT Logger Configuration"""
    output_dir: str = "dataset_output"
    max_queue_size: int = 10000
    flush_interval: float = 1.0  # seconds
    max_batch_size: int = 100
    enable_async: bool = True
    backup_on_error: bool = True


class ShareGPTLogger:
    """High-performance ShareGPT format logger"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config: Optional[ShareGPTLoggerConfig] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[ShareGPTLoggerConfig] = None):
        if self._initialized:
            return

        self.config = config or ShareGPTLoggerConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize queue and thread pool
        self.queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.running = True

        # Start background processing thread
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

        # Register exit handler
        atexit.register(self._cleanup)

        self._initialized = True

    def _worker(self):
        """Background worker thread"""
        batch = []
        last_flush = datetime.now()

        while self.running:
            try:
                # Collect batch data
                while len(batch) < self.config.max_batch_size:
                    try:
                        item = self.queue.get_nowait()
                        if item is None:  # Stop signal
                            self.running = False
                            break
                        batch.append(item)
                    except queue.Empty:
                        break

                # Check if flush is needed
                now = datetime.now()
                should_flush = (
                        len(batch) >= self.config.max_batch_size or
                        (now - last_flush).total_seconds() >= self.config.flush_interval or
                        not self.running
                )

                if batch and should_flush:
                    self._flush_batch(batch)
                    batch.clear()
                    last_flush = now

                # If queue is empty and no forced flush needed, sleep briefly
                if not batch and self.running:
                    threading.Event().wait(0.01)

            except Exception as e:
                print(f"[ShareGPTLogger] Worker error: {e}")
                if self.config.backup_on_error:
                    self._backup_failed_items(batch)
                batch.clear()

    def _flush_batch(self, batch: list):
        """Batch write to files"""
        try:
            for item in batch:
                self._write_single_item(item)
        except Exception as e:
            print(f"[ShareGPTLogger] Batch flush error: {e}")
            if self.config.backup_on_error:
                self._backup_failed_items(batch)

    def _write_single_item(self, item: Dict[str, Any]):
        """Write single entry"""
        try:
            # Construct ShareGPT format
            sharegpt_data = {
                "id": str(uuid.uuid4()),
                "conversations": [
                    {"from": "human", "value": str(item.get("input", ""))},
                    {"from": "gpt", "value": str(item.get("output", ""))}
                ],
                "timestamp": datetime.now().isoformat(),
                "metadata": item.get("metadata", {})
            }

            # Generate file path
            filename = f"{sharegpt_data['id']}.sharegpt.json"
            file_path = self.output_dir / filename

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[ShareGPTLogger] Write error for item: {e}")
            if self.config.backup_on_error:
                self._backup_single_item(item)

    def _backup_single_item(self, item: Dict[str, Any]):
        """Backup failed entry"""
        try:
            backup_dir = self.output_dir / "backup"
            backup_dir.mkdir(exist_ok=True)
            filename = f"failed_{uuid.uuid4()}.json"
            file_path = backup_dir / filename

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(item, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ShareGPTLogger] Backup error: {e}")

    def _backup_failed_items(self, items: list):
        """Batch backup failed entries"""
        for item in items:
            self._backup_single_item(item)

    def log(
            self,
            input_content: Union[str, dict],
            output_content: Union[str, dict],
            metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a conversation data entry

        Args:
            input_content: Input content (prompt)
            output_content: Output content (model response)
            metadata: Metadata
        """
        try:
            item = {
                "input": input_content,
                "output": output_content,
                "metadata": metadata or {}
            }

            if self.config.enable_async:
                # Async mode: put into queue
                try:
                    self.queue.put_nowait(item)
                except queue.Full:
                    print("[ShareGPTLogger] Queue full, dropping item")
            else:
                # Sync mode: write directly
                self._write_single_item(item)

        except Exception as e:
            print(f"[ShareGPTLogger] Log error: {e}")
            if self.config.backup_on_error:
                self._backup_single_item({
                    "input": str(input_content),
                    "output": str(output_content),
                    "metadata": metadata or {},
                    "error": str(e)
                })

    async def alog(
            self,
            input_content: Union[str, dict],
            output_content: Union[str, dict],
            metadata: Optional[Dict[str, Any]] = None
    ):
        """Async logging interface"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.log,
            input_content,
            output_content,
            metadata
        )

    def _cleanup(self):
        """Clean up resources"""
        self.running = False
        if hasattr(self, 'queue'):
            self.queue.put_nowait(None)  # Send stop signal
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

    def flush(self):
        """Force flush all pending data"""
        # Wait for queue to empty
        while not self.queue.empty():
            threading.Event().wait(0.1)


# Global instance
def get_sharegpt_logger(config: Optional[ShareGPTLoggerConfig] = None) -> ShareGPTLogger:
    """Get global ShareGPT Logger instance"""
    return ShareGPTLogger(config)


# Convenience functions
def log_sharegpt_conversation(
        input_content: Union[str, dict],
        output_content: Union[str, dict],
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[ShareGPTLoggerConfig] = None
):
    """Convenient logging function"""
    logger = get_sharegpt_logger(config)
    logger.log(input_content, output_content, metadata)


async def alog_sharegpt_conversation(
        input_content: Union[str, dict],
        output_content: Union[str, dict],
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[ShareGPTLoggerConfig] = None
):
    """Convenient async logging function"""
    logger = get_sharegpt_logger(config)
    await logger.alog(input_content, output_content, metadata)
