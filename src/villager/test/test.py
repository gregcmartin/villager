from scheduler.core.schemas.structure.task_relation_manager import TaskRelationManager, Node, Direction

if __name__ == '__main__':
    """
    A → B → C
    ↓
    D → F → H
    ↓       ↓
    E → G   I
    """


    class T(Node):
        def __init__(self, s):
            super().__init__()
            self.s = s

        def __str__(self):
            return self.s


    manager = TaskRelationManager()
    # 使用字符串作为任务对象
    task_a = T("A")
    task_b = T("B")
    task_c = T("C")
    task_d = T("D")
    task_e = T("E")
    task_f = T("F")
    task_g = T("G")
    task_h = T("H")
    task_i = T("I")
    task_j = T("J")
    task_k = T("K")
    task_l = T("L")

    manager.set_relationship(task_a, Direction.RIGHT, task_b)
    manager.set_relationship(task_a, Direction.DOWN, task_d)
    manager.set_relationship(task_d, Direction.DOWN, task_e)
    manager.set_relationship(task_d, Direction.RIGHT, task_f)
    manager.set_relationship(task_e, Direction.RIGHT, task_g)
    manager.set_relationship(task_b, Direction.RIGHT, task_c)
    manager.set_relationship(task_f, Direction.RIGHT, task_h)
    manager.set_relationship(task_h, Direction.DOWN, task_i)

    # print(manager.get_neighbor_sub_nodes(task_d))
    # print(manager.remove_node(task_d))
    # for it in manager.get_neighbor_sub_nodes(task_d):
    #     print(it)
    # print(manager.get_upper_chain(task_d, 3))
    # manager.add_sub_tasks(task_i, [task_j, task_k, task_l])
    # for Un in manager.get_upper_chain(task_l, 3):
    #     print(f"from:{Un['from_node']};to:{Un['to_node']};direction:{Un['direction']};dis:{Un['distance_with_start']};")

    manager.draw_graph()
