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
        use_enum_values = True  # Enable automatic enum value conversion

    def __str__(self, indent: int = 2) -> str:
        """Recursively format model as YAML format string"""

        def convert_value(value: Any) -> Any:
            """Recursively convert field values to YAML compatible types"""
            if isinstance(value, BaseModel):
                return value.dict()  # Convert Pydantic model to dictionary
            elif isinstance(value, Enum):
                return value.value  # Get enum value
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}  # Recursively process dictionary
            elif isinstance(value, list):
                return [convert_value(v) for v in value]  # Recursively process list
            return value

        # Convert entire model data
        data = {k: convert_value(v) for k, v in self.__dict__.items()}

        # Generate YAML string, use safe_dump to avoid potential security risks
        return yaml.safe_dump(
            data,
            indent=indent,
            allow_unicode=True,  # Support Unicode characters
            default_flow_style=False  # Disable compact format
        )
