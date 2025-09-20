import json
import re
import uuid
from enum import Enum
from typing import Optional, Any

import yaml
from pydantic import BaseModel, Field

from scheduler.core.schemas.schemas import TaskModel, TaskModelOut, TaskStatus


class TaskObject(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_model: TaskModel
    task_out_model: Optional[TaskModelOut]
    task_status_model: TaskStatus

    class Config:
        use_enum_values = True  # 启用枚举值自动转换

    def __str__(self, indent: int = 2) -> str:
        """递归格式化模型为YAML格式字符串"""

        def convert_value(value: Any) -> Any:
            """递归转换字段值为YAML兼容类型"""
            if isinstance(value, BaseModel):
                return value.dict()  # 转换Pydantic模型为字典
            elif isinstance(value, Enum):
                return value.value  # 取枚举值
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}  # 递归处理字典
            elif isinstance(value, list):
                return [convert_value(v) for v in value]  # 递归处理列表
            return value

        # 转换整个模型数据
        data = {k: convert_value(v) for k, v in self.__dict__.items()}

        # 生成YAML字符串，使用safe_dump避免潜在的安全风险
        return yaml.safe_dump(
            data,
            indent=indent,
            allow_unicode=True,  # 支持Unicode字符
            default_flow_style=False  # 禁用紧凑格式
        )
