#-- coding:utf-8
from .ast import ASTNode
from .compute.value import expr_value_calc_funcs,expr_value_prop_funcs
from .compute.width import expr_width_calc_funcs,expr_width_fix_funcs
from .compute.width import expr_match_width,expr_calc_width
from .tools.utility import count_one
import warnings
__all__ = ['Mux','Concatenate','Expr','wrap_expr',
    'BinaryOperator',
    'ConstExpr','Hexadecimal','Decimal','Octal','Binary']
def wrap_expr(expr):
    if isinstance(expr,Expr):return expr
    elif isinstance(expr,int):return Hexadecimal(expr)
    else:raise TypeError('Cannot convert "%s" object into "Expr".'%type(expr))
def propagated(func):
    def propagated_func(*args):
        res = func(*args)
        return res if res is None else res._prop_value()
    return propagated_func
class Expr(ASTNode):
    max_cols_per_line = 120
    @classmethod
    def _need_split_line(cls,codes):
        for lines in codes:
            if len(lines)>1:return True
        length = 0
        for lines in codes:
            for line in lines:
                for word in line:length+=len(word)
        return length>cls.max_cols_per_line
    def _generate(self,indent=0,p_precedence=99):return self._expr_generate_funcs[self.typename](self,indent,p_precedence)
    def _calc_width(self):self._width_calc_func(self)
    def _fix_width(self,expr):return self._width_fix_func(self,expr)
    def _prop_value(self):return self._value_prop_func(self)
    @property
    def typename(self):return self._typename
    @typename.setter
    def typename(self,typename):
        assert isinstance(typename,str)
        self._typename = typename
        self._width_calc_func = expr_width_calc_funcs[typename]
        self._width_fix_func  = expr_width_fix_funcs [typename]
        self._value_calc_func = expr_value_calc_funcs[typename]
        self._value_prop_func = expr_value_prop_funcs[typename]
    @property
    def lhs(self):return self.childs[1]
    @lhs.setter
    def lhs(self,subexpr):self.childs[1] = wrap_expr(subexpr)
    @property
    def rhs(self):return self.childs[0]
    @rhs.setter
    def rhs(self,subexpr):self.childs[0] = wrap_expr(subexpr)
    @property
    def cond(self):return self.childs[2]
    @cond.setter
    def cond(self,cond):
        cond = wrap_expr(cond)
        cond._fix_width(1)
        self.childs[2] = cond
    def __init__(self):raise NotImplementedError()
    def __int__(self):return self._value_calc_func(self)
    def __len__(self):
        if self.width is None:raise ValueError('Getting width of width-free expr "%s".'%str(self))
        if self.width <= 0   :raise ValueError('Found negative width in "%s".'%str(self))
        return self.width
    @property
    def _is_constant(self):return False
    @property
    def length(self):return 1
    def _wrap_constant(self,value):return Hexadecimal(value,width=self.width)
    @staticmethod
    def _hex_value(*args,**kwargs):return Hexadecimal(*args,**kwargs)
    @staticmethod
    def _is_constant_value(expr,value):return isinstance(expr,(int,ConstExpr)) and int(expr)==value
    @staticmethod
    def _is_expr_typename(obj,typename):return isinstance(obj,Expr) and expr._typename == typename
    @propagated
    def __mul__(self,rhs):return self if rhs is None else Concatenate(self,rhs)
    @propagated
    def __pos__(self):return self
    @propagated
    def __pow__(self,rhs):
        if rhs ==0:return None
        else:return Replicate(self,rhs)
    @propagated
    def __lt__ (self,rhs):return BinaryOperator('<',self,rhs)
    @propagated
    def __gt__ (self,rhs):return BinaryOperator('>',self,rhs)
    @propagated
    def __le__ (self,rhs):return BinaryOperator('<=',self,rhs)
    @propagated
    def __ge__ (self,rhs):return BinaryOperator('>=',self,rhs)
    @propagated
    def __add__(self,rhs):return AddOperator(self,rhs)
    @propagated
    def __sub__(self,rhs):return BinaryOperator('-',self,rhs)
    @propagated
    def __and__(self,rhs):return AndOperator(self,rhs)
    @propagated
    def __or__ (self,rhs):return OrOperator(self,rhs)
    @propagated
    def __xor__(self,rhs):return XorOperator(self,rhs)
    @propagated
    def __invert__(self):return UnaryOperator('~',self)
    @propagated
    def __neg__(self):return UnaryOperator(' -',self)
    @propagated
    def __lshift__(self,rhs):return BinaryOperator('<<',self,rhs)
    @propagated
    def __rshift__(self,rhs):return BinaryOperator('>>',self,rhs)
    @propagated
    def __floordiv__(self,rhs):return BinaryOperator('==',self,rhs)
    @propagated
    def validif(self,cond):return ValidIf(cond,self)
    @propagated
    def mux(self,lhs,rhs):return Mux(self,lhs,rhs)
    @propagated
    def multiply_operate(self,rhs):return MulOperator(self,rhs)
    @propagated
    def divide_operate(self,rhs):return DivOperator(self,rhs)
    @propagated
    def module_operate(self,rhs):return ModOperator(self,rhs)
    @propagated
    def equal_to(self,rhs):return BinaryOperator('==',self,rhs)
    @propagated
    def not_equal_to(self,rhs):return BinaryOperator('!=',self,rhs)
    @propagated
    def reduce_or(self):return UnaryOperator(' |',self)
    @propagated
    def reduce_and(self):return UnaryOperator(' &',self)
    @propagated
    def reduce_xor(self):return UnaryOperator(' ^',self)
    def __getitem__(self,key):raise SyntaxError('Invalid fetch "[%s]" from expr "%s".'%(str(key),str(self)))
    def __rpow__(self,lhs):return wrap_expr(lhs)**self
    def __rmul__(self,lhs):return self if lhs is None else wrap_expr(lhs)*self
    def __radd__(self,lhs):return wrap_expr(lhs)+self
    def __rsub__(self,lhs):return wrap_expr(lhs)-self
    def __rand__(self,lhs):return wrap_expr(lhs)&self
    def __ror__(self,lhs) :return wrap_expr(lhs)|self
    def __rxor__(self,lhs):return wrap_expr(lhs)^self
    def __rfloordiv__(self,lhs):return wrap_expr(lhs)//self
    @staticmethod
    def full_adder_c(a,b,c):
        return a&b|a&c|b&c
    @staticmethod
    def full_adder_s(a,b,c):
        return a^b^c
    def _set_default(self,typename,n_childs=0):
        self.comments = []
        self.typename = typename
        self.childs = [None]*ASTNode._expr_n_childs[typename]
        self.value = None
        self.width = None
    def _connect_port(self,m,p):
        if p.io!='input':raise KeyError('Assigning "%s" to %s port "%s"'%(str(self),p.io,str(p)))
        self._fix_width(p)
class UnaryOperator(Expr):
    def __init__(self,typename,rhs):
        self._set_default(typename)
        self.rhs = rhs
        self._calc_width()
class BinaryOperator(Expr):
    def __init__(self,typename,lhs,rhs):
        self._set_default(typename)
        self.rhs = rhs
        self.lhs = lhs
        self._calc_width()
class Mux(Expr):
    def __init__(self,cond,lhs,rhs):
        self._set_default('?:')
        self.rhs = rhs
        self.lhs = lhs
        self.cond = cond
        self._calc_width()
class MultilineAlignOperator(Expr):
    @property
    def _display_as_long(self):return self._display_as_long_val
    @_display_as_long.setter
    def _display_as_long(self,as_long):
        if not isinstance(as_long,bool):raise TypeError('Type of "long" should be bool')
        self._display_as_long_val = as_long
class AssociativeOperator(MultilineAlignOperator):
    def _merge_childs(self,other):
        other = wrap_expr(other)
        if other._typename==self._typename:
            self._display_as_long|=other._display_as_long
            self.childs.extend(other.childs)
        else:self.childs.append(other)
    def __init__(self,typename,lhs,rhs,long=False):
        self._display_as_long = long
        self._set_default(typename)
        lhs = wrap_expr(lhs)
        rhs = wrap_expr(rhs)
        expr_calc_width(lhs,rhs)
        self._merge_childs(lhs)
        self._merge_childs(rhs)
        self._calc_width()
class OrOperator(AssociativeOperator):
    def __init__(self,lhs,rhs,long=False):AssociativeOperator.__init__(self,'|',lhs,rhs,long)
    def __ior__(self,other):
        expr_calc_width(self,other)
        self._merge_childs(other)
        return self
class AndOperator(AssociativeOperator):
    def __init__(self,lhs,rhs,long=False):AssociativeOperator.__init__(self,'&',lhs,rhs,long)
    def __iand__(self,other):
        expr_calc_width(self,other)
        self._merge_childs(other)
        return self
class AddOperator(AssociativeOperator):
    def __init__(self,lhs,rhs,long=False):AssociativeOperator.__init__(self,'+',lhs,rhs,long)
    def __iadd__(self,other):
        expr_calc_width(self,other)
        self._merge_childs(other)
        return self
class XorOperator(AssociativeOperator):
    def __init__(self,lhs,rhs,long=False):AssociativeOperator.__init__(self,'^',lhs,rhs,long)
    def __ixor__(self,other):
        expr_calc_width(self,other)
        self._merge_childs(other)
        return self
def fix_slice(key,width):
    start = (0 if key.step is None else key.stop-key.step) if key.start is None else key.start
    stop  = (width if key.step is None else key.start+key.start) if key.stop is None else key.stop
    width = stop - start
    return start,stop,width
class Concatenate(AssociativeOperator):
    def _extract_childs(self,args):
        for arg in args:
            if isinstance(arg,(tuple,list)):self._extract_childs(arg)
            else:self._merge_childs(arg)
    def __init__(self,*args,long=False):
        self._display_as_long = long
        self._set_default('{}')
        self._extract_childs(args)
        self._calc_width()
    def __setitem__(self,key,val):
        if not isinstance(key,slice):raise TypeError(type(key))
        expr_match_width(val,len(self))
        start,stop,width = fix_slice(key,len(self))
        base = 0
        for expr in self.childs:
            if stop < base or start > base + len(expr):continue
            if start > base:
                expr[start-base:] = val[:base-start+len(expr)]
            elif stop<base +len(expr):
                expr[:stop-base] = val[-(stop-base):]
            else:
                expr[:] = val[base-start::len(expr)]
            base += len(expr)
class ValidIf(BinaryOperator):
    def __init__(self,lhs,rhs):
        self._set_default('validif')
        self.rhs = rhs
        self.lhs = lhs
        self._calc_width()
class MulOperator(BinaryOperator):
    def __init__(self,lhs,rhs):
        self._set_default('*')
        self.rhs = rhs
        self.lhs = lhs
        self._calc_width()
class DivOperator(BinaryOperator):
    def __init__(self,lhs,rhs):
        self._set_default('/')
        self.rhs = rhs
        self.lhs = lhs
        self._calc_width()
class ModOperator(BinaryOperator):
    def __init__(self,lhs,rhs):
        self._set_default('%')
        self.rhs = rhs
        self.lhs = lhs
        self._calc_width()
class Replicate(UnaryOperator):
    @property
    def count(self):return self._count
    @count.setter
    def count(self,count):
        count=int(count)
        self._count = count
        if count<=0:raise ValueError('Invalid replicate "%s".'%self)
    def __init__(self,rhs,count):
        self._set_default('{{}}')
        self.rhs = rhs
        self.count = count
        self._calc_width()
class ConstExpr(Expr):
    _radix_fmtstrs  = {
        16:lambda width,value:("%d'h{:0>%dx}"%(width,(width+3)//4)).format(value),
        10:lambda width,value:("%d'd{:0>d}"  % width              ).format(value),
        8 :lambda width,value:("%d'o{:0>%do}"%(width,(width+2)//3)).format(value),
        2 :lambda width,value:("%d'b{:0>%db}"%(width, width      )).format(value)}
    @property
    def radix(self):return self._radix
    @radix.setter
    def radix(self,radix):
        if radix not in {2,8,10,16}:raise ValueError('Invalid radix.')
        self._radix = radix
        self._radix_fmtstr = self._radix_fmtstrs[radix]
    @staticmethod
    def _convert_str(value):
        y = 0
        for i in range(len(x)):
            y<<=8
            c = ord(x[i])
            y |=c
            if c>=256 or c<0:raise RuntimeError('Charset Error')
        return y
    @property
    def value(self):return self._value
    @value.setter
    def value(self,value):
        if value is None:self._value = value
        else:
            if isinstance(value,str):self._value = self._convert_str(value)
            else:self._value = int(value)
            if not self._width is None:self._value&=(1<<self._width)-1
    @property
    def width(self):return self._width
    @width.setter
    def width(self,width):
        if not isinstance(width,int):raise TypeError(type(width),width)
        if width<=0:raise ValueError('Constant value with non-positive width.')
        self._width = width
        if not self._value is None:self._value&=(1<<self._width)-1
    @property
    def _driven(self):return 0 if self._value is None else self._constant
    @property
    def _constant(self):return -1 if self._width is None else (1<<self._width)-1
    @property
    def _is_constant(self):return True
    def _set_default(self,typename,n_childs=0):
        self.comments = []
        self.childs = [None]*n_childs
        self.value = None
        self.width = None
    def __init__(self,value,width=None,radix=10):
        self.typename = 'const'
        self._value = 0
        self._width = None
        if not width is None:self.width = width
        self.radix = radix
        self.value = value
    def __getitem__(self,key):
        if isinstance(key,slice):
            for a in {'start','stop','step'}:
                if not isinstance(getattr(key,a),(int,type(None))):
                    raise SyntaxError('Invalid fetch format from constant expression.') 
            start = 0 if key.start is None else key.start
            if not key.step is None:return Hexadecimal(int(self)>>start,width=key.step)
            elif not key.stop is None:return Hexadecimal(int(self)>>start,width=key.stop-start)
            return Hexadecimal(int(self)>>start,width=self.width-start)
        elif isinstance(key,(int,ConstExpr)):
            loc = int(key)
            if loc<0:loc += len(self)
            return Binary((self.value>>loc)&1,width=1)
        elif isinstance(key,Expr):
            n = 1<<len(key)
            v = self.value
            m = count_one(v)
            if m==0:return Binary(0,width=1)
            elif m==n:return Binary(1,width=1)
            else:
                if m<=(n>>1):
                    expr = 0
                    for i in range(n):
                        if ((v>>i)&1)==1:expr|=key//i
                else:
                    expr = 1
                    for i in range(n):
                        if ((v>>i)&1)==0:expr&=~(key//i)
                return expr
        else:raise TypeError(type(key))
    def __str__(self):
        width = self.width
        value = self.value
        if value is None:
            if width is None:return "'bz"
            else:return "%d'bz"%width
        if width is None:
            if value<0:warnings.warn('Negative value without width declared.')
            return str(value)
        result = self._radix_fmtstr(width,value)
        return result
    def __int__(self):return self.value
    def __eq__(self,other):
        if isinstance(other,ConstExpr):return self.width==other.width and int(self)==int(other)
        elif isinstance(other,int):return self.width is None and int(self)==other
        else:return False
    def __hash__(self):return int(self)+(0 if self.width is None else self.width)
def Hexadecimal(x,width=None):
    if width==0:return None
    else:return ConstExpr(x,width=width,radix=16)
def Binary     (x,width=None):
    if width==0:return None
    else:return ConstExpr(x,width=width,radix=2 )
def Octal      (x,width=None):
    if width==0:return None
    else:return ConstExpr(x,width=width,radix=8 )
def Decimal    (x,width=None):
    if width==0:return None
    else:return ConstExpr(x,width=width,radix=10)
