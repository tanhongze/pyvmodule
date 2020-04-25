from .ast import ASTNode
from .naming import NamingRecv
from .expr import wrap_expr,Expr
from .compute.width import expr_match_width,expr_calc_width
from .compute.driver import ControlBlockDriverChecker as DriverChecker
__all__ = ['ControlBlock','Always','Initial','AlwaysDelay','When']
class ControlBlock(ASTNode,NamingRecv):
    _n_childs = ASTNode._controlblock_n_childs
    lines_show_pairing = 10
    @property
    def typename(self):return self._typename
    @typename.setter
    def typename(self,typename):
        self._typename = typename
    def _generate(self,indent=0):return self._cblk_generate_funcs[self.typename](self,indent)
    @property
    def parent(self):return None
    @parent.setter
    def parent(self,parent):raise NotImplementedError()
    @property
    def body(self):
        node = self.childs[0]
        if isinstance(node,When) and not node.prev is None:
            node = node.prev
            while not node.prev is None:node = node.prev
            self.childs[0] = node
        return node
    @body.setter
    def body(self,val):
        if not self.childs[0] is None:raise ValueError('Cannot reset body of control block')
        if isinstance(val,ControlBlock):
            while True:
                if val.typename == 'if':
                    if isinstance(val.cond,int) and val.cond==0:
                        prev = val.prev
                        next = val.next
                        if prev is None:
                            if not next is None:next.prev = None
                            val = next
                            break
                        else:
                            if not next is None:next.prev = None
                            prev.next = None
                            prev.next = next
                            val = prev
                            continue
                elif val.typename != 'else':raise RuntimeError('Invalid nested control block "%s"'%val.typename)
                if val.prev is None:break
                val = val.prev
            if val is None:return
            val.parent = self
            self._driver_checker.set_child(val._driver_checker)
        else:
            val = wrap_expr(val)
            self.width = val.width
        self.childs[0] = val
    def __init__(self):raise NotImplementedError()
    def __len__(self):
        if self.width is None:raise NotImplementedError()
        else:return self.width
    @property
    def next(self):return None
    @property
    def prev(self):return None
    def _fix_width(self,expected):
        if expr_match_width(self,expected):
            self.body._fix_width(expected)
            if not self.next is None:self.next._fix_width(expected)
    def _set_default(self,typename,name):
        self.typename = typename
        self.name = name
        self.value = None
        self.comments = []
        self.childs = [None]*self._n_childs[typename]
        self.assignments = []
        self.functions = []
        self.width = None
        self._driver_checker = DriverChecker()
    def __getitem__(self,key):
        if isinstance(key,slice):
            y = key.start
            if not isinstance(y,ASTNode):raise TypeError(type(y))
            typename = y.typename
            x = key.stop

            if not key.step is None:
                if x is None:
                    for name in key.step:
                        self[getattr(y,name):]
                elif isinstance(key.step,dict):
                    for tname,sname in key.step.items():
                        self[getattr(y,tname):getattr(x,sname)]
                else:
                    for name in key.step:
                        self[getattr(y,name):getattr(x,name)]
                return self
            if typename == 'struct':
                if x is None:
                    for name,item in key._naming_var.items():
                        self[item:]
                else:
                    for name,item in key._naming_var.items():
                        if hasattr(x,name):self[item:getattr(x,name)]
            else:
                if x is None:
                    if isinstance(self.body,Expr):self[y:self.body]
                    elif self.body is None:pass
                    else:self.body[y:]
                    if not self.next is None:self.next[y:]
                else:
                    # When(cond)[y:x]
                    if typename == 'wire':raise TypeError('Control block cannot set value for wire "%s".'%str(y))
                    if typename == 'reg':
                        target = y
                        mask = (1<<len(y))-1
                    elif typename == '[]':
                        target = y._get_target()
                        mask   = y._range_mask
                    else:raise TypeError(typename)
                    target._append_controlblock(self)
                    x = wrap_expr(x)
                    x._fix_width(y)
                    self.assignments.append((y,x))
                    if self._driver_checker.add(id(target),mask):raise KeyError('Multi-driven signal "%s" is detected.'%y)
        elif isinstance(key,ASTNode) and key.typename=='function':
            self.functions.append(key)
        else:
            self.body = key
        return self
    def _get_drive_mask(self,target):
        if not isinstance(target,ASTNode) or target.typename!='reg':raise TypeError(type(target))
        mask = self._driver_checker.get_mask(id(target))
        return mask
class Always(ControlBlock):
    @property
    def cond(self):return self.childs[1]
    @cond.setter
    def cond(self,val):
        if val is None:return
        val._fix_width(1)
        self.childs[1] = wrap_expr(val)
    def __init__(self,cond=None,edge='posedge',name=None):
        self._set_default('always@',name)
        self.edge = edge
        self.cond = cond
class Initial(ControlBlock):
    def _get_drive_mask(self,target):return 0
    def __init__(self,body=None,name=None):
        self._set_default('initial',name)
        if not body is None:self.body = body
class AlwaysDelay(ControlBlock):
    def __init__(self,delay,name=None):
        assert isinstance(delay,int)
        self._set_default('always#',name)
        self.delay = delay
class Else(ControlBlock):
    @property
    def parent(self):
        if not self._prev is None:return self._prev.parent
        else:return self._parent
    @parent.setter
    def parent(self,parent):
        if parent is None:return
        if not isinstance(parent,ControlBlock):e_unhandled_type(parent)
        if self.parent is None:self._parent = parent
        elif not self.parent is parent:
            print(self.parent.typename)
            print(self.parent.name)
            print(parent.typename)
            print(parent.name)
            raise ValueError('Sharing parent between control blocks')
    @property
    def prev(self):
        return self._prev
    @prev.setter
    def prev(self,prev):
        if prev is None:
            if self.parent is None:
                if self._prev is None:pass
                else:self._prev.next = None
            else:raise ValueError('Cannot modify belonging of If- or Else- control block.')
        elif not isinstance(val,(When,Else)):raise TypeError('Need If- or Else- control block, not ',type(val))
        else:prev.next = self
    def __init__(self,name=None):
        self._parent = None
        self._set_default('else',name)
    def _set_default(self,typename,name):
        ControlBlock._set_default(self,typename,name)
        self._prev = None
class When(Else):
    @property
    def cond(self):return self.childs[1]
    @cond.setter
    def cond(self,val):
        if val is None:return
        val._fix_width(1)
        self.childs[1] = wrap_expr(val)
    @property
    def next(self):return self.childs[2]
    @next.setter
    def next(self,val):
        if val is None:
            if self.parent is None:
                if self.next is None:pass
                else:
                    self.next._prev = None
                    self.childs[2] = None
            else:raise ValueError('Cannot modify belonging of If- or Else- control block.')
        elif not isinstance(val,(When,Else)):raise TypeError('Need When- or Else- control block, not ',type(val))
        elif not self.next is None or not val.prev is None:raise ValueError('Cannot modify belonging of If- or Else- control block.')
        self.childs[2] = val
        self.parent = val.parent
        val.parent = self.parent
        val._prev = self
        self._fix_width_next(val)
        self._driver_checker.set_brother(val._driver_checker)
    def _fix_width_next(self,next):
        if next.width is None:
            if self.width is None:return
            while not next is None:
                next.width = self.width
                if not next.body is None:next.body._fix_width(self.width)
                next = next.next
        elif self.width is None:
            prev = self
            while not prev is None:
                prev.width = next.width
                if not prev.body is None:prev.body._fix_width(next.width)
                prev = prev.prev
    def __init__(self,condition,name=None):
        self._parent = None
        self._set_default('if',name)
        self.cond = condition
    @property
    def Otherwise(self):
        self.next = Else()
        return self.next
    def When(self,condition,name=None):
        self.next = type(self)(condition,name=name)
        return self.next
