#----------------------------------------------------------------------
#pyvmodule:expr.py
#
#Copyright (C) 2019  Hong Ze Tan
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.
#----------------------------------------------------------------------
from .ast import ASTNode
from .check import VChecker
from .calculations import actions as calc_actions
from .language.common import precedences
from .naming import NamingNode
import warnings
__all__ = ['Wire','Reg','Mux','Concatenate','BitReduce','Reduce','Hexadecimal','Decimal','Octal','Binary','Always','Initial','AlwaysDelay','When','ASTNode','Expr','ControlBlock','Index']
cols__split_line = 80
def report__unhandled_type(expr):
    raise TypeError(type(expr))
def wrap_expr(expr):
    if isinstance(expr,(Expr,Index,ControlBlock)):
        return expr
    elif isinstance(expr,(int,str)):
        return Hexadecimal(expr)
    elif isinstance(expr,list):
        return [wrap_expr(e) for e in expr]
    else:
        report__unhandled_type(expr)
def width__calculate(expr):
    assert isinstance(expr,(Expr,ControlBlock))
    if not hasattr(expr,'width'):
        expr.width = None
    if isinstance(expr,ControlBlock):
        if expr.prev!=None:
            if expr.lhs.width!=None and expr.prev.width!=None:
                VChecker.match(expr.lhs,expr.prev)
            elif expr.lhs.width!=None:
                VChecker.fix_width(expr.get__first(),expr.lhs)
            elif expr.prev.width!=None:
                VChecker.fix_width(expr.lhs,expr.prev)
        if expr.lhs.width!=None:
            expr.width = len(expr.lhs)
        return
    # check & fix
    if expr.typename in {'&','&&','|','||','^','+','-','<','>','<=','>=','==','!=','?:'} or (expr.typename=='if' and expr.next!=None):
        if expr.lhs.width!=None and expr.rhs.width!=None:
            VChecker.match(expr.lhs,expr.rhs)
        elif expr.lhs.width!=None:
            VChecker.fix_width(expr.rhs,expr.lhs)
        elif expr.rhs.width!=None:
            VChecker.fix_width(expr.lhs,expr.rhs)
    if expr.typename in {'*','{}','<','>','<=','>=','==','!=',' ^',' |',' &','<<','>>'}:
        for child in expr.childs:
            if child.width==None:
                VChecker.match()
    elif expr.typename in {'**','{{}}'}:
        VChecker.match(expr.lhs)
    elif expr.typename == '[]':
        if not isinstance(expr.lhs,(Wire,Fetch)):
            report__unhandled_type(expr.lhs)
        def check_subexpr(subexpr,length):
            if isinstance(subexpr,ConstExpr):
                VChecker.index(int(subexpr),length)
            elif isinstance(subexpr,Expr):
                VChecker.fix_width(subexpr,None)
            else:
                return False
            return True
        def check_range(subexpr,width):
            if isinstance(subexpr,Index):
                if subexpr.step!=1:
                    raise ValueError('Invalid step %d'%subexpr.step)
                VChecker.index(subexpr.stop,width,allow_eq=True)
                VChecker.index(subexpr.start,width,allow_eq=False)
            else:
                return False
            return True
        if expr.lhs.typename in {'wire','reg'} and expr.lhs.length>1:
            # access as a RAM
            if isinstance(expr.rhs,tuple):
                assert len(expr.rhs)==2
                if check_subexpr(expr.rhs[0],expr.lhs.length):
                    report__unhandled_type(expr.rhs[0])
                if check_range(expr.rhs[1],expr.lhs.width):
                    pass
                elif check_subexpr(expr.rhs[1],expr.lhs.width):
                    pass
                else:
                    report__unhandled_type(expr.rhs[1])
            elif check_subexpr(expr.rhs,expr.lhs.length):
                pass
            else:
                report__unhandled_type(expr.rhs)
        else:
            if check_range(expr.rhs,expr.lhs.width):
                pass
            elif check_subexpr(expr.rhs,expr.lhs.width):
                pass
            else:
                report__unhandled_type(expr.rhs)
    elif expr.typename in {' |',' &',' ^'}:
        VChecker.fix_width(expr.rhs,None)
    # compute
    if expr.typename in {'&','&&','|','||','^','+','-','~','!',' ',' -','?:'}:
        expr.width = expr.rhs.width
    elif expr.typename in {' |',' &',' ^'}:
        expr.width = 1
    elif expr.typename in {'*','{}'}:
        width = 0
        for child in expr.childs:
            width+=child.width
        expr.width=width
    elif expr.typename in {'<','>','<=','>=','==','!=',' ^',' |',' &'}:
        expr.width = 1
    elif expr.typename in {'>>','<<'}:
        expr.width = expr.lhs.width
    elif expr.typename == '[]':
        def get_fetch_width(subexpr):
            if isinstance(subexpr,Index):
                return subexpr.stop-subexpr.start
            elif isinstance(subexpr,Expr):
                return 1
            else:
                report__unhandled_type(subexpr)
        if expr.lhs.typename in {'wire','reg'} and expr.lhs.length>1:
            if isinstance(expr.rhs,tuple):
                expr.width = get_fetch_width(expr.rhs)
            else:
                expr.width = len(expr.lhs)
        else:
            expr.width = get_fetch_width(expr.rhs)
    elif expr.typename in {'**','{{}}'}:
        expr.width = expr.lhs.width*int(expr.rhs)
    else:
        raise NotImplementedError('"%s"'%expr.typename)
    if expr.width!=None:
        VChecker.fix_width(expr,None)
class Index(ASTNode):
    def check_index_type(self,index):
        if isinstance(index,ConstExpr):
            index = int(index)
        if not isinstance(index,int):
            report__unhandled_type(index)
        return index
    def check_index(self,index,context,allow_eq=False):
        index = self.check_index_type(index)
        if index>len(context):
            raise IndexError('Index is out of range.')
        if index==len(context) and not allow_eq:
            raise IndexError('Index is out of range.')
        if index<0:
            index_fixed = len(context)+index
            if index_fixed<0:
                raise IndexError('Negative index.')
            index = index_fixed
        return index
    @property
    def v__long(self):
        return False
    def __init__(self,key,context):
        if isinstance(key,int):
            self.start = key
            self.stop  = key+1
            self.step  = 1
        elif isinstance(key,slice):
            if key.start!=None:
                self.start = key.start
            else:
                self.start = 0
            if key.stop!=None:
                self.stop = key.stop
            else:
                self.stop = len(context)
            if key.step!=None:
                self.step = key.step
            else:
                self.step = 1
        elif isinstance(key,Index):
            self.start = key.start
            self.stop = key.stop
            self.step = key.step
        else:
            report__unhandled_type(index)
        if self.stop==self.start:
            raise IndexError('Invalid range width zero-width.')
        self.typename = 'range'
        self.start = self.check_index(self.start,context,allow_eq=False)
        self.stop = self.check_index(self.stop,context,allow_eq=True)
        self.step = self.check_index_type(self.step)
        self.width = (self.stop-self.start+self.step-1)//self.step
        if self.stop<=self.start:
            raise IndexError('Invalid range index direction "%s".'%str(self))
    def __str__(self):
        assert self.step==1
        return ''.join([str(self.stop-1),':',str(self.start)])
    def __len__(self):
        return self.width
    def __hash__(self):
        return self.start*10007+self.stop*7+self.step*17
    def __eq__(self,other):
        if not isinstance(other,Index):
            return False
        return self.start==other.start and self.stop==other.stop and self.step==other.step
class Expr(ASTNode):
    def __init__(self):
        # width lhs rhs typename long indent comments
        raise NotImplementedError()
    @property
    def precedence(self):
        return precedences[self.typename]
    @property
    def lhs(self):
        return self.childs[0]
    @property
    def rhs(self):
        return self.childs[1]
    @property
    def cond(self):
        return self.childs[2]
    def get__str(self,expr,same=False):
        item = str(expr)
        if isinstance(expr,Expr):
            if expr.precedence>self.precedence:
                item = '(%s)'%item
            elif same and expr.precedence==self.precedence:
                item = '(%s)'%item
        return item
    def __str__(self):
        raise NotImplementedError()
    def __int__(self):
        return calc_actions[self.typename](*self.childs)
    def __mul__(self,rhs):
        if rhs == None:
            return self
        expr = Concatenate([self,rhs])
        return expr
    def __rmul__(self,lhs):
        if lhs == None:
            return self
        expr = Concatenate([lhs,self])
        return expr
    def __pow__(self,rhs):
        if not isinstance(rhs,(int,ConstExpr)):
            report__unhandled_type(rhs)
        if int(rhs)==0:
            raise ValueError('zero-width.')
        if int(rhs)==1:
            return self
        return Replicate(self,rhs)
    def __len__(self):
        if self.width!=None and self.width>0:
            return self.width
        if hasattr(self,'name'):
            name = self.name
        else:
            name = 'anonymous'
        if self.width==None:
            raise NotImplementedError('"%s" with none-width'%name)
        if self.width<=0:
            raise NotImplementedError('"%s" with non-positive-width'%name)
        raise NotImplementedError('"%s" error'%name)
    def __lt__(self,rhs):
        return LeftJoinOperator('<',self,rhs)
    def __add__(self,rhs):
        expr = AbelianOperator('+',self,rhs)
        if isinstance(expr.lhs,ConstExpr) and int(expr.lhs)==0:
            return expr.rhs
        if isinstance(expr.rhs,ConstExpr) and int(expr.rhs)==0:
            return expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)+int(expr.rhs),width=expr.width)
        return expr
    def __radd__(self,lhs):
        expr = AbelianOperator('+',lhs,self)
        if isinstance(expr.lhs,ConstExpr) and int(expr.lhs)==0:
            return expr.rhs
        if isinstance(expr.rhs,ConstExpr) and int(expr.rhs)==0:
            return expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)+int(expr.rhs),width=expr.width)
        return expr
    def __sub__(self,rhs):
        expr = LeftJoinOperator('-',self,rhs)
        if isinstance(expr.lhs,ConstExpr) and int(expr.lhs)==0:
            return -expr.rhs
        if isinstance(expr.rhs,ConstExpr) and int(expr.rhs)==0:
            return expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)-int(expr.rhs),width=expr.width)
        return expr
    def __rsub__(self,lhs):
        expr = LeftJoinOperator('-',lhs,self)
        if isinstance(expr.lhs,ConstExpr) and int(expr.lhs)==0:
            return -expr.rhs
        if isinstance(expr.rhs,ConstExpr) and int(expr.rhs)==0:
            return expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)-int(expr.rhs),width=expr.width)
        return expr
    def __and__(self,rhs):
        expr = AbelianOperator('&',self,rhs)
        if isinstance(expr.lhs,ConstExpr):
            if int(expr.lhs)==0:
                return Decimal(0,width=self.width)
            elif expr.lhs.width!=None:
                if int(expr.lhs)==(1<<len(expr.lhs))-1:
                    return expr.rhs
        if isinstance(expr.rhs,ConstExpr):
            if int(expr.rhs)==0:
                return Decimal(0,width=self.width)
            elif expr.rhs.width!=None:
                if int(expr.rhs)==(1<<len(expr.rhs))-1:
                    return expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)&int(expr.rhs),width=expr.width)
        return expr
    def __rand__(self,lhs):
        expr = AbelianOperator('&',lhs,self)
        if isinstance(expr.lhs,ConstExpr):
            if int(expr.lhs)==0:
                return Decimal(0,width=self.width)
            elif expr.lhs.width!=None:
                if int(expr.lhs)==(1<<len(expr.lhs))-1:
                    return expr.rhs
        if isinstance(expr.rhs,ConstExpr):
            if int(expr.rhs)==0:
                return Decimal(0,width=self.width)
            elif expr.rhs.width!=None:
                if int(expr.rhs)==(1<<len(expr.rhs))-1:
                    return expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)&int(expr.rhs),width=expr.width)
        return expr
    def __or__(self,rhs):
        expr = AbelianOperator('|',self,rhs)
        if isinstance(expr.lhs,ConstExpr):
            if int(expr.lhs)==0:
                return expr.rhs
            elif expr.lhs.width!=None:
                if int(expr.lhs)==(1<<len(expr.lhs))-1:
                    return Hexadecimal(-1,width=len(expr.lhs))
        if isinstance(expr.rhs,ConstExpr):
            if int(expr.rhs)==0:
                return expr.lhs
            elif expr.rhs.width!=None:
                if int(expr.rhs)==(1<<len(expr.rhs))-1:
                    return Hexadecimal(-1,width=len(expr.rhs))
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)|int(expr.rhs),width=expr.width)
        return expr
    def __ror__(self,lhs):
        expr = AbelianOperator('|',lhs,self)
        if isinstance(expr.lhs,ConstExpr):
            if int(expr.lhs)==0:
                return expr.rhs
            elif expr.lhs.width!=None:
                if int(expr.lhs)==(1<<len(expr.lhs))-1:
                    return Hexadecimal(-1,width=len(expr.lhs))
        if isinstance(expr.rhs,ConstExpr):
            if int(expr.rhs)==0:
                return expr.lhs
            elif expr.rhs.width!=None:
                if int(expr.rhs)==(1<<len(expr.rhs))-1:
                    return Hexadecimal(-1,width=len(expr.rhs))
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)|int(expr.rhs),width=expr.width)
        return expr
    def __xor__(self,rhs):
        expr = AbelianOperator('^',self,rhs)
        if isinstance(expr.lhs,ConstExpr):
            if int(expr.lhs)==0:
                return expr.rhs
            elif expr.lhs.width!=None:
                if int(expr.lhs)==(1<<len(expr.lhs))-1:
                    return ~expr.rhs
        if isinstance(expr.rhs,ConstExpr):
            if int(expr.rhs)==0:
                return expr.lhs
            elif expr.rhs.width!=None:
                if int(expr.rhs)==(1<<len(expr.rhs))-1:
                    return ~expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)^int(expr.rhs),width=expr.width)
        return expr
    def __rxor__(self,lhs):
        expr = AbelianOperator('^',lhs,self)
        if isinstance(expr.lhs,ConstExpr):
            if int(expr.lhs)==0:
                return expr.rhs
            elif expr.lhs.width!=None:
                if int(expr.lhs)==(1<<len(expr.lhs))-1:
                    return ~expr.rhs
        if isinstance(expr.rhs,ConstExpr):
            if int(expr.rhs)==0:
                return expr.lhs
            elif expr.rhs.width!=None:
                if int(expr.rhs)==(1<<len(expr.rhs))-1:
                    return ~expr.lhs
        if isinstance(expr.lhs,ConstExpr) and isinstance(expr.rhs,ConstExpr):
            return ConstExpr(int(expr.lhs)^int(expr.rhs),width=expr.width)
        return expr
    def __invert__(self):
        if isinstance(self,LeftJoinOperator):
            invert_ops = {'==':'!=','!=':'==','<=':'>','>=':'<','>':'<=','<':'>='}
            if self.typename in invert_ops:
                return LeftJoinOperator(invert_ops[self.typename],self.lhs,self.rhs)
        expr = UnaryOperator('~',self)
        if isinstance(self,UnaryOperator):
            if self.typename in {'~','!'}:
                return self.rhs
        return expr
    def __pos__(self):
        return UnaryOperator(' ',self)
    def __neg__(self):
        if isinstance(self,UnaryOperator) and self.typename==' -':
            return self.rhs
        return UnaryOperator(' -',self)
    def __lshift__(self,rhs):
        return ShiftOperator('<<',self,rhs)
    def __rshift__(self,rhs):
        return ShiftOperator('>>',self,rhs)
    def __floordiv__(self,rhs):
        return LeftJoinOperator('==',self,rhs)
    def __rfloordiv__(self,lhs):
        return LeftJoinOperator('==',lhs,self)
    def __getitem__(self,key):
        raise RuntimeError('Invalid syntax, fetching from expr.')
    def cut__off(self):
        if self.width!=None and self.value!=None:
            self.value&=(1<<len(self))-1
    def append__childs(self,*childs):
        for child in childs:
            self.childs.append(wrap_expr(child))
            self.childs[-1].parent = self
    def set__default(self,typename):
        self.comments = []
        self.parents = []
        self.childs = []
        self.value = None
        self.typename = typename
class BinaryOperator(Expr):
    def __init__(self,typename,lhs,rhs):
        self.set__default(typename)
        self.append__childs(lhs,rhs)
        width__calculate(self)
class UnaryOperator(Expr):
    def __init__(self,typename,rhs):
        self.set__default(typename)
        self.append__childs(rhs)
        width__calculate(self)
    @property
    def rhs(self):
        return self.childs[0]
    def __str__(self):
        rhs = self.get__str(self.rhs)
        return self.typename+rhs
class LeftJoinOperator(BinaryOperator):
    def __str__(self):
        lhs = self.get__str(self.lhs,same=(self.typename!='-'))
        rhs = self.get__str(self.rhs,same=True)
        return '%s %s %s'%(lhs,self.typename,rhs)
class AssociativeOperator(BinaryOperator):
    def __init__(self,typename,lhs,rhs,long=False):
        self.set__default(typename)
        self.append__childs(lhs,rhs)
        width__calculate(self)
        self.long = long
class AbelianOperator(AssociativeOperator):
    def __str__(self):
        spliter = ' %s '%self.typename
        items = []
        for child in self.childs:
            expr_str = self.get__str(child,same=False)
            items.append(expr_str)
        sentence = spliter.join(items)
        return sentence
class Mux(Expr):
    def __init__(self,cond,lhs,rhs):
        self.set__default('?:')
        VChecker.fix_width(cond,1)
        self.append__childs(lhs,rhs,cond)
        width__calculate(self)
    def __str__(self):  
        cond = self.get__str(self.cond)
        lhs = self.get__str(self.lhs)
        rhs = self.get__str(self.rhs)
        return '%s?%s:%s'%(cond,lhs,rhs)
class Concatenate(AssociativeOperator):
    def append__childs_expanded(self,wires):
        if isinstance(wires,Expr):
            if wires.typename == self.typename:
                self.childs.extend(wires.childs)
                for child in wires.childs:
                    child.parents.append(self)
            else:
                self.childs.append(wires)
                wires.parents.append(self)
        elif isinstance(wires,list) or isinstance(wires,tuple):
            for wire in wires:
                self.append__childs_expanded(wire)
        elif isinstance(wires,dict):
            for key in wires:
                wire = wires[key]
                self.append__childs_expanded(wire)
        else:
            raise TypeError('Undetermined width.')
    def __init__(self,exprs,long=False):
        self.set__default('{}')
        self.append__childs_expanded(exprs)
        width__calculate(self)
        self.long = long
    def __setitem__(self,key,val):
        if not isinstance(key,slice):
            report__unhandled_type(key)
        else:
            if key.start!=None or key.stop!=None or key.step!=None:
                raise KeyError('Invalid part-selection of concatenate block.')
        base = 0
        for expr in self.childs:
            if isinstance(expr,Wire):
                expr[:] = val[base:base+len(expr)]
                base += len(expr)
            elif isinstance(expr,Expr):
                raise TypeError('Cannot set value to expression "%s".'%str(expr))
            else:
                report__unhandled_type(expr)
        VChecker.match(val,base)
    def __str__(self):
        spliter = ','
        items = []
        for i in range(len(self.childs)-1,-1,-1):
            items.append(str(self.childs[i]))
        items = ['{',spliter.join(items),'}']
        sentence = ''.join(items)
        return sentence
    def __int__(self):
        retval = 0
        if len(self.childs)>0:
            retval = int(self.childs[-1])
            for i in range(len(self.childs)-2,-1,-1):
                retval<<=len(self.childs[i])
                retval |=int(self.childs[i])
        return retval
class Replicate(Expr):
    def check__replication(self):
        if not isinstance(self.rhs,ConstExpr):
            report__unhandled_type(rhs)
        elif int(self.rhs)<=0:
            raise ValueError('Non-positive replication.')
    def __init__(self,lhs,rhs):
        self.set__default('{{}}')
        self.append__childs(lhs,rhs)
        self.check__replication()
        width__calculate(self)
    def __str__(self):
        return '{%d{%s}}'%(int(self.rhs),str(self.lhs))
class Wire(Expr,NamingNode):
    random_init = False
    def receive__args(self,args,width,expr):
        if len(args)>1:
            raise KeyError('Too many arguments.')
        for arg in args:
            if isinstance(arg,ConstExpr):
                raise SyntaxWarning('Ambitious parameter, value or width?')
            elif isinstance(arg,Expr) or isinstance(arg,ControlBlock):
                if expr!=None:
                    raise ValueError('Multi-driven wire detected.')
                if width!=None:
                    VChecker.fix_width(arg,width)
                expr = arg
                width = len(expr)
            elif isinstance(arg,int):
                if width!=None:
                    raise ValueError('Multiple specified width detected.')
                width = arg
            elif isinstance(arg,list):
                expr = Concatenate(arg)
                width = len(expr)
            else:
                report__unhandled_type(arg)
        if width==None:
            width = 1
        return width,expr
    def __str__(self):
        return self.name
    def set__default(self,typename):
        self.comments = []
        self.assignments = []
        self.typename = typename
        self.used = set()
        self.parents = []
    def compute(self):
        value = 0
        masks = 0
        for key,val in self.assignments:
            if key.typename=='range':
                index = int(key.start)
                mask = ((1<<len(key))-1)<<index
            else:
                index = int(key)
                mask = 1<<index
            value|= (int(val)<<index)&mask
            if mask&masks!=0:
                warnings.warn('Repeated assignments')
            masks|= mask
        if masks+1!=(1<<len(self)):
            warnings.warn('Missing assignments')
        return value
    def __init__(self,*args,width=None,length=1,name=None,io=None,expr=None,reverse=False,bypass=False,wire_type='wire',**pragmas):
        self.set__default(wire_type)
        NamingNode.__init__(self,name=name,reverse=reverse,bypass=bypass)
        VChecker.identifier(self.name)
        self.io = VChecker.port(io,length,wire_type)
        width,expr = self.receive__args(args,width,expr)
        self.width,self.length = VChecker.shape(width,length)
        self.value = None
        if self.length>1:
            self.value = [None for i in range(self.length)]
        self.pragmas = pragmas
        if expr!=None:
            self[:] = expr
    def __int__(self):
        if self.length==1:
            if self.value!=None:
                return self.value
            if self.random_init:
                self.value = random.randint(1<<len(self))
                return self.value
        raise NotImplementedError('Not initialized.')
    def decorate__subscript(self,key,val=None):
        if isinstance(key,slice):
            key = Index(key,self)
            if key.step!=1:
                return key
        if isinstance(key,(int,ConstExpr)):
            index = int(key)
            if index<0:
                index+=len(self)
            if index<0:
                raise IndexError('Negative index %d.'%(index-len(self)))
            VChecker.index(index,self.length if self.length>1 else len(self),allow_eq=False)
            if isinstance(key,int):
                key = ConstExpr(index)
            else:
                key.value = index
        if self.length>1:
            if isinstance(key,Index):
                raise TypeError('Invalid "[]" expr, %s'%str(key))
        else:
            assert self.length==1
            if isinstance(key,tuple):
                raise TypeError('Invalid "[]" expr, %s.'%(str(tuple(str(arg) for arg in key))))
            
        if isinstance(key,tuple):
            if len(key)!=2 or isinstance(key[0],slice):
                raise KeyError('Invalid format'%str(key))
            if self.length<=1:
                raise KeyError('Invalid format for non-ram-like assignment'%str(key))
            if isinstance(key[1],(slice,Index)):
                key = (wrap_expr(key[0]),Index(key[1],self))
                width = len(key[1])
            else:
                key = (wrap_expr(key[0]),wrap_expr(key[1]))
                width = 1
            if isinstance(key[1],ConstExpr):
                VChecker.index(key[1],len(self),allow_eq=False)
            if isinstance(key[0],ConstExpr):
                VChecker.index(key[0],self.length,allow_eq=False)
        elif isinstance(key,Index):
            width = len(key)
        elif isinstance(key,Expr):
            width = self.width if self.length>1 else 1
            if isinstance(key,ConstExpr):
                if self.length>1:
                    VChecker.index(int(key),self.length)
                else:
                    VChecker.index(int(key),len(self))
        else:
            report__unhandled_type(key)
        if val!=None:
            VChecker.fix_width(val,width)
        return key
    def __getitem__(self,key):
        key = self.decorate__subscript(key)
        if isinstance(key,Index) and key.step!=1:
            return Concatenate([self[i] for i in range(key.start,key.stop,key.step)])
        def simplifying_fetch_index(expr,key):
            if isinstance(key,Index):
                if key.start==0 and key.stop==len(expr) and key.step==1:
                    return expr
                elif len(key)==1:
                    return expr[key.start]
                elif key.step==1:
                    return Fetch(expr,key)
                else:
                    raise NotImplementedError()
            if isinstance(key,ConstExpr):
                if int(key)==0 and len(expr)==1:
                    return expr
            if isinstance(expr,Expr):
                return Fetch(expr,key)
            raise TypeError('Unexpected index type "%s" for fetching.'%str(type(key)))
        if isinstance(key,tuple):
            expr = Fetch(self,key[0])
            return simplifying_fetch_index(expr,key[1])
        return simplifying_fetch_index(self,key)
    def __setitem__(self,key,val):
        if val==None:
            raise ValueError('assigning None to wire "%s".'%str(self))
        if self.io=='input':
            raise TypeError('Could not set value to input signal.')
        val = wrap_expr(val)
        if isinstance(val,ControlBlock):
            if self.typename!='reg':
                raise ValueError('Invalid control block for "%s".'%self.typename)
            while val.prev!=None:
                val = val.prev
        elif isinstance(val,Expr):
            if self.typename!='wire':
                raise ValueError('Invalid control block for "%s".'%self.typename)
        else:
            report__unhandled_type(val)
        key = self.decorate__subscript(key,val=val)
        self.assignments.append((key,val))
    def copy(self):
        return Wire(width=self.width,length=self.length,io=self.io)
    def __eq__(self,other):
        return self is other
def Reg(*args,**kwargs):
    if 'wire_type' in kwargs:
        raise KeyError('duplicated wire_type specifying "%s".'%kwargs['wire_type'])
    return Wire(*args,wire_type='reg',**kwargs)
class Fetch(LeftJoinOperator):
    @property
    def length(self):return 1
    def __init__(self,lhs,rhs):
        self.set__default('[]')
        self.append__childs(lhs,rhs)
        assert isinstance(lhs,(Wire,Fetch))
        width__calculate(self)
    def __int__(self):
        if isinstance(self.lhs.value,list):
            return self.lhs.value[int(self.rhs)]
        elif isinstance(self.rhs,Expr):
            return (int(self.lhs)>>int(self.rhs))&1
        elif isinstance(self.rhs,Index):
            return (int(self.lhs)>>int(self.rhs.start))&((1<<len(self.rhs))-1)
        else:
            report__unhandled_type(self.rhs)
    decorate__subscript = Wire.decorate__subscript
    __getitem__ = Wire.__getitem__
    def __str__(self):
        if isinstance(self.rhs,Index):
            return '%s[%s:%s]'%(str(self.lhs),str(self.rhs.stop-1),str(self.rhs.start))
        elif isinstance(self.rhs,Expr):
            return '%s[%s]'%(str(self.lhs),str(self.rhs))
        else:
            report__unhandled_type(self.rhs)
class ConstExpr(Expr):
    def convert__value(self,x):
        if isinstance(x,int):
            return x
        elif isinstance(x,str):
            y = 0
            for i in range(len(x)):
                y<<=8
                c = ord(x[i])
                y |=c
                if c>=256 or c<0:
                    raise RuntimeError('Charset Error')
            return y
        elif x==None:
            return x
        else:
            report__unhandled_type(x)
    def __init__(self,x,width=None,radix=10):
        self.set__default('const')
        self.width = width
        self.radix = radix
        self.value = self.convert__value(x)
        self.cut__off()
        if radix not in {2,8,10,16}:
            raise ValueError('Invalid radix.')
    def __getitem__(self,key):
        if isinstance(key,slice):
            val = 0
            if key.step!=1:
                for i in range(key.start,key.stop,key.step):
                    val<<=1
                    val|=(self.value>>i)&1
            else:
                val = (self.value>>self.start)&((1<<self.stop)-1)
            return val
        key = wrap_expr(key)
        if isinstance(key,ConstExpr):
            return (self.value>>int(key))&1
        if isinstance(key,Expr):
            expr = 0
            for i in range(1<<len(key)):
                expr|=key//i
            return expr
    def __str__(self):
        if self.value==None:
            return "{%d{1'bz}}"%len(self)
        x = int(self)
        radix = self.radix
        if x<0:
            if self.width!=None:
                x&= (1<<len(self))-1
            else:
                warnings.warn('no width declared.')
                return str(x)
        digits = []
        i = 0
        while x != 0:
            digits.append(x%radix)
            x//=radix
            i+= radix_lengths[radix]
        if len(digits)==0:
            digits.append(0)
            i = radix_lengths[radix]
        if self.width!=None:
            while i<self.width:
                digits.append(0)
                i+= radix_lengths[radix]
        parts = []
        if self.width!=None:
            parts.append(str(len(self)))
            parts.append(radix_names[radix])
        elif radix!=10:
            parts.append(radix_names[radix])
        for i in range(len(digits)-1,-1,-1):
            parts.append('%x'%digits[i])
        return ''.join(parts)
    def __int__(self):
        self.cut__off()
        return self.value
    def __eq__(self,other):
        if not isinstance(other,ConstExpr):
            return False
        return self.width==other.width and int(self)==int(other)
    def __hash__(self):
        return int(self)+(self.width if self.width else 0)
def Hexadecimal(x,width=None):
    return ConstExpr(x,width=width,radix=16)
def Binary(x,width=None):
    return ConstExpr(x,width=width,radix=2)
def Octal(x,width=None):
    return ConstExpr(x,width=width,radix=8)
def Decimal(x,width=None):
    return ConstExpr(x,width=width,radix=10)
bitreduce_operators = {'|':' |','|':' |','&':' &',' &':' &','^':' ^',' ^':' ^'}
bitreduce_identities= {' |':Binary(0,width=1),' ^':Binary(0,width=1),'&':Binary(1,width=1)}
abelian_actions = {'&':lambda lhs,rhs:lhs&rhs,
    '|':lambda lhs,rhs:lhs|rhs,
    '^':lambda lhs,rhs:lhs^rhs,
    '+':lambda lhs,rhs:lhs+rhs,
    '&~':lambda lhs,rhs:lhs&~rhs,
    '|~':lambda lhs,rhs:lhs|~rhs}
def BitReduce(typename,expr):
    if typename not in bitreduce_operators:
        raise RuntimeError('Unexpected bitwise-reduction operator "%s".'%typename)
    typename = bitreduce_operators[typename]
    if isinstance(expr,list):
        if len(expr)==0:
            return bitreduce_identities[typename]
        if len(expr)==1:
            return BitReduce(typename,expr[0])
        expr = Concatenate(expr)
    if len(expr)==1:
        return expr
    return UnaryOperator(typename,expr)
def Reduce(typename,exprs,long=False):
    if typename not in abelian_actions:
        raise KeyError('Invalid reduce operation.')
    assert isinstance(exprs,list)
    if typename in {'&','&~'}:
        expr = Hexadecimal(-1)
    else:
        expr = Hexadecimal(0)
    if len(exprs)<=0:
        return expr
    elif len(exprs)==1:
        if typename in {'|~','&~'}:
            return ~exprs[0]
        else:
            return exprs[0]
    else:
        for w in exprs:
            expr = abelian_actions[typename](expr,w)
        if isinstance(expr,ConstExpr):
            warnings.warn('Reduction of constant values in target code, values "%s" as below.'%str(expr))
        else:
            expr.long = long
        return expr
radix_names = {16:"'h",10:"'d",8:"'o",2:"'b"}
radix_lengths={16:4,10:3,8:3,2:1}
class ControlBlock(ASTNode):
    @property
    def lhs(self):
        return self.childs[0]
    @property
    def cond(self):
        return self.childs[1]
    @property
    def rhs(self):
        return self.childs[2]
    @property
    def body(self):
        return self.childs[0]
    @property
    def next(self):
        return self.childs[2]
    def set__body(self,body):
        self.childs[0] = wrap_expr(body)
        self.childs[0].parents.append(self)
        width__calculate(self)
        return self
    def set__cond(self,cond):
        if cond!=None:
            VChecker.fix_width(cond,1)
        self.childs[1] = wrap_expr(cond)
        self.childs[1].parents.append(self)
    def set__next(self,next):
        self.childs[2] = wrap_expr(next)
        self.childs[2] = wrap_expr(next)
        self.childs[2].prev = self
        self.childs[2].parents.append(self)
        return next
    def __init__(self):
        # childs typename width comments indent
        raise NotImplementedError()
    def __len__(self):
        if self.width!=None:
            return self.width
        raise NotImplementedError()
    def __int__(self):
        return int(self.lhs)
    def get__first(self):
        target = self
        while target.prev!=None:
            target = target.prev
        return target
    def set__default(self,typename):
        self.name = None
        self.value = None
        self.comments = []
        self.parents = []
        self.childs = [None,None,None]
        self.prev = None
        self.width = None
        self.typename = typename
    def __getitem__(self,key):
        if isinstance(key,ControlBlock):
            if key.typename not in {'if','else'}:
                raise RuntimeError('Invalid nested control block "%s"'%key.typename)
            key = key.get__first()
        else:
            if not isinstance(key,Expr):
                key = Hexadecimal(key)
        return self.set__body(key)
    def Next(self,next):
        return self.set__next(next)
    def cut__off(self):
        if self.width!=None and self.value!=None:
            self.value&=(1<<len(self))-1
class Always(ControlBlock):
    def __init__(self,cond=None,edge='posedge'):
        self.set__default('always@')
        self.edge = edge
        self.set__cond(cond)
def AlwaysInit(clock,reset,init=0):
    cond = When(reset)
    al = Always(clock)[cond]
    if reset.name[-1]=='n':
        other = cond
        cond.Otherwise[init]
    else:
        cond[init]
        other = cond.Otherwise
    def Inner(key):
        other[key]
        return al
    al.Inner = Inner
    return al
class Initial(ControlBlock):
    def __init__(self,body=None):
        self.set__default('initial')
        if body!=None:
            self.set__body(body)
class AlwaysDelay(ControlBlock):
    def __init__(self,delay):
        assert isinstance(delay,int)
        self.set__default('always#')
        self.delay = delay
class Else(ControlBlock):
    def __init__(self,cond_if):
        self.set__default('else')
        self.cond_if = cond_if
class When(ControlBlock):
    def __init__(self,condition):
        self.set__default('if')
        self.set__cond(condition)
    @property
    def Otherwise(self):
        return self.Next(Else(self.cond))
    def When(self,condition):
        return self.Next(type(self)(condition))