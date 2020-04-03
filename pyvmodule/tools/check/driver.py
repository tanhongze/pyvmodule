from pyvmodule.ast import ASTNode
def alert_multidriven(func):
    def alert_func(*args):
        if func(*args):raise KeyError('Multi-driven signal is detected.')
    return alert_func
class ControlBlockDriverChecker:
    def __init__(self,init=None):
        self.masks = {} if init is None else init
        self.total = {} if init is None else init.copy()
        self.brothers = [self]
        self.parent = None
        self.child = None
    def assert_non_overlap(self,masks,id,area):
        return (masks.get(id,0)&area)!=0
    def insert_parent_total(self,id,area):
        cur = self.parent
        while not cur is None:
            if self.assert_non_overlap(cur.masks,id,area):return True
            cur.total[id] = cur.total.get(id,0)|area
            cur = cur.parent
        return False
    def union(self,other):
        for id,area in self.masks.items():
            self.add_item(id,area)
    def get_mask(self,id):
        return self.total.get(id,0)
    def copy(self):
        return ControlBlockDriverChecker(self.masks.copy())
    @alert_multidriven
    def add(self,id,area):
        flag = False
        if not self.child is None:
            if self.assert_non_overlap(self.child.total,id,area):flag = True
        elif self.assert_non_overlap(self.masks,id,area):flag = True
        else:
            self.masks[id] = self.masks.get(id,0)|area
            self.total[id] = self.total.get(id,0)|area
            if self.insert_parent_total(id,area):flag = True
        return flag
    @alert_multidriven
    def set_brother(self,other):
        brothers = self.brothers+other.brothers
        parent = other.parent if self.parent is None else self.parent
        total = self.total
        for id,area in other.total.items():
            total[id] = total.get(id,0)|area
            if self.insert_parent_total(id,area):return True
        for brother in brothers:
            brother.brothers = brothers
            brother.total = total
            if brother.parent is None:brother.parent = parent
            elif not brother.parent is parent:raise RuntimeError('Shared parent.')
        return False
    @alert_multidriven
    def set_child(self,child):
        self.child = child
        child.parent = self
        for id,area in child.total.items():
            if child.insert_parent_total(id,area):return True
        return False
