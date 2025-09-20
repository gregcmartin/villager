# -*- coding: utf-8 -*-
import asyncio
import os
import traceback
import uuid
from typing import Dict
from fastapi import FastAPI

from scheduler.core.init import global_llm
from scheduler.core.mcp_client.mcp_client import McpClient
from scheduler.core.schemas.schemas import TaskModel
from scheduler.core.schemas.structure.task_relation_manager import TRM
from scheduler.core.tasks.task import TaskNode
from config import MCP
from config import SERVER_UUID

mcp_client_baseurl = MCP['client']['base_url']


class Task:
    def __init__(self, token, status, graph_context, abstract, description, verification, context):
        self.token = token
        self.status = status

        self.graph_context = graph_context
        self.abstract = abstract
        self.description = description
        self.verification = verification
        self.context = context

    def to_dict(self):
        return {
            'token': self.token,
            'status': self.status,
            'graph_context': self.graph_context,
            'abstract': self.abstract,
            'description': self.description,
            'verification': self.verification,
        }

    def set_graph(self, graph):
        self.graph_context = graph
        return self


# 全局任务状态管理器
task_manager: Dict[str, dict] = {}


def boot(app: FastAPI):
    # 创建任务并后台运行
    async def run_background_task(task_id, abstract, description, verification):
        graph_name = f'./{task_id}.mermaid'

        def blocking_task():
            try:
                # 检查任务是否已被取消
                if task_manager[task_id]['status'] == 'cancelled':
                    return

                with global_llm():
                    with TRM() as trm:
                        # 检查任务是否已被取消
                        if task_manager[task_id]['status'] == 'cancelled':
                            return
                        mcp_client = McpClient(mcp_client_base_url=mcp_client_baseurl, task_id=task_id)
                        _task = TaskNode(
                            task_model=TaskModel(abstract=abstract, description=description, verification=verification),
                            trm=trm,
                            mcp_client=mcp_client,
                            graph_name=graph_name
                        )
                        task_manager[task_id]['mcp_client'] = mcp_client
                        # 检查任务是否已被取消
                        if task_manager[task_id]['status'] == 'cancelled':
                            return
                        for i in range(3):
                            try:
                                result = _task.execute()
                                break
                            except Exception as e:
                                traceback.print_exc()

                        # 检查任务是否已被取消
                        if task_manager[task_id]['status'] == 'cancelled':
                            return

                        task_manager[task_id]['status'] = 'completed'
                        task_manager[task_id]['result'] = result

            except Exception as e:
                print(f"Background task {task_id} failed: {e}")
                traceback.print_exc()
                task_manager[task_id]['status'] = 'failed'

        task_manager[task_id] = {
            "status": "running",
            "graph_name": graph_name,
            "abstract": abstract,
            "description": description,
            "verification": verification,

        }
        try:
            await asyncio.to_thread(blocking_task)
        except Exception as e:
            print(f"Background task {task_id} failed: {e}")
            traceback.print_exc()

    @app.post("/task")
    async def post_task(abstract: str, description: str, verification: str):

        # 启动后台任务
        asyncio.create_task(run_background_task(SERVER_UUID, abstract, description, verification))

        return {"task_id": SERVER_UUID}

    @app.get("/get/task/status")
    async def get_task_status():
        tasks = []
        for task_id in task_manager.keys():
            graph_name = task_manager[task_id]['graph_name']
            graph_context = ""
            if os.path.exists(graph_name):
                with open(graph_name, 'r') as f:
                    graph_context = f.read()
            tasks.append(Task(token=task_id, status=task_manager[task_id]["status"], graph_context=graph_context,
                              abstract=task_manager[task_id]["abstract"],
                              description=task_manager[task_id]["description"],
                              verification=task_manager[task_id]["verification"],
                              context=task_manager[SERVER_UUID]['mcp_client'].context
                              )
                         )
        return tasks

    @app.get("/tree")
    async def get_tree(task_id: str):
        task_info = task_manager.get(task_id)
        if not task_info:
            return {"error": "Task not found"}

        graph_name = task_info['graph_name']
        if not os.path.exists(graph_name):
            return {"status": task_info['status'], "message": "Graph file not ready yet."}

        with open(graph_name, 'r') as f:
            content = f.read()
        return {"status": task_info['status'], "graph": content}

    @app.get('/task/{task_id}/tree')
    async def get_tree_v1(task_id: str):
        return get_tree(task_id=task_id)

    @app.put("/task/{task_id}/stop")
    async def stop_task(task_id: str):
        task_info = task_manager.get(task_id)
        if not task_info:
            return {"error": "Task not found"}, 404

        if task_info['status'] != 'running':
            return {"message": f"Task is {task_info['status']}"}, 400

        # 标记任务为已取消
        task_info['status'] = 'cancelled'
        return {"message": f"Task {task_id} has been marked as cancelled"}

    @app.get('/task/{tasK_id}/context')
    async def get_context(task_id: str):
        return task_manager[task_id]['mcp_client'].context
