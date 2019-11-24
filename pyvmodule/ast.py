class ASTNode:
    global_object_id = 0
    def __hash__(self):
        return str(self).__hash__()
    def __eq__(self,other):
        return self is other