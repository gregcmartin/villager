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
    """ShareGPT Logger 配置"""
    output_dir: str = "dataset_output"
    max_queue_size: int = 10000
    flush_interval: float = 1.0  # 秒
    max_batch_size: int = 100
    enable_async: bool = True
    backup_on_error: bool = True


class ShareGPTLogger:
    """高性能 ShareGPT 格式日志记录器"""

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

        # 初始化队列和线程池
        self.queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.running = True

        # 启动后台处理线程
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

        # 注册退出处理
        atexit.register(self._cleanup)

        self._initialized = True

    def _worker(self):
        """后台工作线程"""
        batch = []
        last_flush = datetime.now()

        while self.running:
            try:
                # 收集批次数据
                while len(batch) < self.config.max_batch_size:
                    try:
                        item = self.queue.get_nowait()
                        if item is None:  # 停止信号
                            self.running = False
                            break
                        batch.append(item)
                    except queue.Empty:
                        break

                # 检查是否需要刷新
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

                # 如果队列为空且不需要强制刷新，短暂休眠
                if not batch and self.running:
                    threading.Event().wait(0.01)

            except Exception as e:
                print(f"[ShareGPTLogger] Worker error: {e}")
                if self.config.backup_on_error:
                    self._backup_failed_items(batch)
                batch.clear()

    def _flush_batch(self, batch: list):
        """批量写入文件"""
        try:
            for item in batch:
                self._write_single_item(item)
        except Exception as e:
            print(f"[ShareGPTLogger] Batch flush error: {e}")
            if self.config.backup_on_error:
                self._backup_failed_items(batch)

    def _write_single_item(self, item: Dict[str, Any]):
        """写入单个条目"""
        try:
            # 构造 ShareGPT 格式
            sharegpt_data = {
                "id": str(uuid.uuid4()),
                "conversations": [
                    {"from": "human", "value": str(item.get("input", ""))},
                    {"from": "gpt", "value": str(item.get("output", ""))}
                ],
                "timestamp": datetime.now().isoformat(),
                "metadata": item.get("metadata", {})
            }

            # 生成文件路径
            filename = f"{sharegpt_data['id']}.sharegpt.json"
            file_path = self.output_dir / filename

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[ShareGPTLogger] Write error for item: {e}")
            if self.config.backup_on_error:
                self._backup_single_item(item)

    def _backup_single_item(self, item: Dict[str, Any]):
        """备份失败的条目"""
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
        """批量备份失败条目"""
        for item in items:
            self._backup_single_item(item)

    def log(
            self,
            input_content: Union[str, dict],
            output_content: Union[str, dict],
            metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录一条对话数据

        Args:
            input_content: 输入内容（prompt）
            output_content: 输出内容（模型响应）
            metadata: 元数据
        """
        try:
            item = {
                "input": input_content,
                "output": output_content,
                "metadata": metadata or {}
            }

            if self.config.enable_async:
                # 异步模式：放入队列
                try:
                    self.queue.put_nowait(item)
                except queue.Full:
                    print("[ShareGPTLogger] Queue full, dropping item")
            else:
                # 同步模式：直接写入
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
        """异步记录接口"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.log,
            input_content,
            output_content,
            metadata
        )

    def _cleanup(self):
        """清理资源"""
        self.running = False
        if hasattr(self, 'queue'):
            self.queue.put_nowait(None)  # 发送停止信号
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

    def flush(self):
        """强制刷新所有待处理数据"""
        # 等待队列清空
        while not self.queue.empty():
            threading.Event().wait(0.1)


# 全局实例
def get_sharegpt_logger(config: Optional[ShareGPTLoggerConfig] = None) -> ShareGPTLogger:
    """获取全局 ShareGPT Logger 实例"""
    return ShareGPTLogger(config)


# 便捷函数
def log_sharegpt_conversation(
        input_content: Union[str, dict],
        output_content: Union[str, dict],
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[ShareGPTLoggerConfig] = None
):
    """便捷的日志记录函数"""
    logger = get_sharegpt_logger(config)
    logger.log(input_content, output_content, metadata)


async def alog_sharegpt_conversation(
        input_content: Union[str, dict],
        output_content: Union[str, dict],
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[ShareGPTLoggerConfig] = None
):
    """便捷的异步日志记录函数"""
    logger = get_sharegpt_logger(config)
    await logger.alog(input_content, output_content, metadata)
