from .ast import ASTNode
from .expr import Expr,wrap_expr,BinaryOperator
from .naming import NamingNode
from .ctrlblk import Always,When,Else,ControlBlock
from .exceptions import a_value_positive,a_width_positive,e_unhandled_type
__all__ = ['Index','Wire','Reg','Fetch']
class Wire(Expr,NamingNode):
    random_init = False
    def __str__(self):return self.name
    @property
    def assignment(self):
        if self.length>1:raise TypeError('Cannot get assignment 2D-array.')
        if self._driven!=(1<<len(self))-1:raise ValueError('Assignment of wire is not completed.')
        self.assignments = sorted(self.assignments,key=lambda entry:entry[0].start)
        return Concatenate([val for key,val in self.assignments])
    @assignment.setter
    def assignment(self,expr):
        self.assignments.clear()
        self._driven = 0
        self._constant = 0
        self[:] = expr
    @property
    def io(self):return self._io
    @io.setter
    def io(self,io):
        if io is None:pass
        elif not isinstance(io,str):raise TypeError('Invalid Use str to represent io type.')
        elif io not in {'input','output','auto'}:raise SyntaxError('Invalid port type "%s".'%io)
        self._io = io
    @property
    def width(self):
        return self._width
    @width.setter
    def width(self,width):
        a_width_positive(width,self)
        self._width = width
    @property
    def length(self):return 1
    @length.setter
    def length(self,length):assert length==1
    @property
    def clock(clock):return None
    @length.setter
    def clock(self,clock):raise NameError('Cannot set clock for wire.')
    @property
    def _range_mask(self):return (1<<len(self))-1
    def _set_default(self,typename):
        self.comments = []
        self.assignments = []
        self.typename = typename
        self._width = 1
        self._length = 1
        self._used = True
        self._driver_port = None
        self._driven = 0
        self._constant = 0
    def _receive_args(self,args,width,expr):
        if len(args)>1:raise KeyError('Too many arguments.')
        else:arg = None if len(args)==0 else args[0]
        if arg is None or isinstance(arg,int):
            if width is None:
                if arg is None:
                    if expr is None:width = 1
                    else:width = len(expr)
                else:width = arg
            else:
                if arg is None:pass
                elif arg!=width:raise ValueError('Multiple specified width detected.')
            self.width = width
            if not expr is None:self[:] = expr
        elif isinstance(arg,ASTNode):
            typename = arg.typename
            if typename=='const':raise SyntaxWarning('Ambitious parameter, value or width?')
            elif not expr is None:raise ValueError('Passed "%s" and "%s", multiple expressions.'%(arg,expr))
            else:
                self.width = len(arg) if width is None else width
                self[:] = arg
        else:e_unhandled_type(arg)
    def __init__(self,*args,width=None,name=None,io=None,expr=None,**pragmas):
        NamingNode.__init__(self,name=name)
        self._set_default('wire')
        self.io = io
        self._receive_args(args,width,expr)
        self.pragmas = pragmas
    def _node_clone(self):
        other = Wire(width=self.width,io=self.io,**self.pragmas)
        other.comments.extend(self.comments)
        return other
    def __len__(self):return self.width
    def __int__(self):
        raise NotImplementedError('Getting static value from non-static variable.')
        if self.length==1:
            if self.value is None:
                if self.random_init:
                    self.value = random.randint(1<<len(self))
                    return self.value
                else:raise NotImplementedError('Not initialized.')
            else:return self.value
        else:raise NotImplementedError('Implicitly get value from 2D-array.')
    def __getitem__(self,key):
        key = Index(key,self)
        if key.typename=='range' and key.start==0 and key.stop==self.width:
            if self.length==1:return self
            else:raise KeyError('Invalid slicing of 2D-array.')
        else:return Fetch(self,key)
    def _mark_driven(self,mask=None):
        if self.io=='input':raise TypeError('Could not set value to input signal "%s".'%str(self))
        if mask is None:mask = (1<<len(self))-1
        if self._driven&mask:raise KeyError('Signal "%s" Multi-driven.'%self)
        self._driven|=mask
        return mask
    def _wrap_value(self,val,width):
        if self._typename=='wire' or not isinstance(val,ControlBlock):
            val = wrap_expr(val)
            allowed_types = Expr
        elif isinstance(val,(When,Else)):
                while not val.prev is None:val = val.prev
        val._fix_width(width)
        return val
    def __setitem__(self,key,val):
        if self.length>1:self[key][:] = val
        else:
            key = Index(key,self)
            if self._typename == 'wire' and key.typename != 'range':raise ValueError('Assigning wire "%s" with non-constant index.'%str(self))
            mask = self._mark_driven(key._range_mask)
            val = self._wrap_value(val,len(key))
            if val.typename=='const':self._constant|=mask
            self.assignments.append((key,val))
    def _connect_port(self,submodule,target):
        if target.io == 'auto':
            if target._driven==0:target.io='input'
            else:target.io='output'
        if target.io == 'output':
            self._mark_driven()
            self._driver_port = (submodule,target)
    def _get_target(self):return self
    def _gen_target(self,key):
        if isinstance(key,tuple):
            assert len(key)==2
            return self[key[0]][key[1]]
        else:return self[key]
    def _verilog_gen_assignment(self,key,val):
        lines = [['assign ']]
        codes = self._gen_target(key)._generate(indent=4)
        lines[-1].extend(codes[0 ])
        lines    .extend(codes[1:])
        lines[-1].append(' = ')
        codes = val._generate()
        lines[-1].extend(codes[0])
        lines    .extend(codes[1:])
        lines[-1].append(';')
        return lines
    def _verilog_gen_pragmas(self,myindent=''):
        return [myindent+self._verilog_gen_pragma(key,val) for key,val in self.pragmas.items()]
    @staticmethod
    def _verilog_gen_pragma(key,val):
        if isinstance(val,str):return '(* %s = "%s" *)'%(key,val)
        if isinstance(val,int):return '(* %s = %d *)'%(key,val)
        if isinstance(val,bool):return '(* %s = %s*)'%(key,'"true"' if val else '"false"')
        if val==None:return '(* %s *)'%key
        raise TypeError()
    def _verilog_comment_driven(self):
        if self.io=='input':return ''
        if self._driven==self._range_mask:return ''
        #warnings.warn(str(w)+' is not fully driven.')
        if self._driven==0:return '// unconnected'
        locs = []
        for i in range(len(self)):
            if (self._driven>>i)&1:locs.append(str(i))
        return '// unconnected, at bit'+','.join(locs)
class Reg(Wire):
    @property
    def io(self):return self._io
    @io.setter
    def io(self,io):
        if io is None:pass
        elif not isinstance(io,str):raise TypeError('Invalid Use str to represent io type.')
        elif io not in {'output'}:
            if io=='input':raise SyntaxError('Invalid port type "input" for register.')
            elif io=='auto':io='output'
            else:raise SyntaxError('Invalid port type "%s".'%io)
        elif self.length>1:raise ValueError('RAM could not be port.')
        self._io = io
    @property
    def length(self):return self._length
    @length.setter
    def length(self,length):
        a_value_positive(length,'depth of memory')
        if length>1 and not self.io is None:raise ValueError('RAM could not be port.')
        self._length = length
    @property
    def assignment(self):raise TypeError('Cannot get assignment of registers.')
    @assignment.setter
    def assignment(self,expr):raise TypeError('Cannot set assignment for registers.')
    def __init__(self,*args,width=None,length=1,name=None,io=None,expr=None,**pragmas):
        NamingNode.__init__(self,name=name)
        self._set_default('reg')
        self._clock = None
        self._length = 1
        self.controlblocks = []
        self.io = io
        self.length = length
        self._receive_args(args,width,expr)
        self.pragmas = pragmas
    def _node_clone(self):
        other = Wire(width=self.width,length=self.length,io=self.io,**self.pragmas)
        other.comments.extend(self.comments)
        return other
    @property
    def clock(self):return self._clock
    @clock.setter
    def clock(self,clock):
        if clock is None:
            if self._clock is None:raise ValueError('Invalid using of default clock, variable clock is not defined.')
            else:return
        else:
            if self._clock is None:pass
            elif clock is self._clock:return
            else:raise ValueError('A register can only belong to one clock-domain.')
        if not isinstance(clock,Wire):raise TypeError('Type of clock must be wire or reg.')
        if clock.width!=1 or clock.width!=1:raise WidthError('Invalid signal size for clock.')
        self._clock = clock
    def _fix_clock(self,blk):
        while not blk.parent is None:blk = blk.parent
        if blk.typename in {'always@','always#','initial'}:return blk
        else:return Always(self.clock)[blk]
    def _append_controlblock(self,blk):
        while not blk.parent is None:blk = blk.parent
        self.controlblocks.append(blk)
    def _wrap_assignment(self,val):
        if not isinstance(val,ControlBlock):blk = Always(self.clock)[wrap_expr(val)]
        else:blk = self._fix_clock(val)
        return blk
    def _refresh_controlblocks(self):
        self.controlblocks = [self._fix_clock(blk) for blk in self.controlblocks]
        for key,val in self.assignments:
            if isinstance(key,tuple):
                target = self
                for k in key:target = target[k]
                self.controlblocks.append(self._wrap_assignment(val)[target:])
            else:self.controlblocks.append(self._wrap_assignment(val)[self[key]:])
        self.assignments.clear()
        self._refresh_driven()
    def _refresh_driven(self):
        self._driven = 0
        repeating = set()
        i = 0
        while i < len(self.controlblocks):
            blk = self.controlblocks[i]
            if id(blk) not in repeating:
                repeating.add(id(blk))
                self._mark_driven(blk._get_drive_mask(self))
                i+=1
            else:del self.controlblocks[i]
def is_const_type(index):
    if isinstance(index,int):return True
    else:return isinstance(index,ASTNode) and index.typename=='const'
def check_const_type(index):
    if is_const_type(index):return int(index)
    else:e_unhandled_type(index)
def repair_const_type(index,width,allow_eq):
    if (index-allow_eq)>=width:raise IndexError('Index is out of range.')
    if index<0:index+=width
    if index<0:raise IndexError('Negative index.')
    return index
def check_const_repair(index,width,allow_eq):
    return repair_const_type(check_const_type(index),width,allow_eq)
class Index(ASTNode):
    @property
    def _range_mask(self):return ((1<<self.width)-1)<<self.start if self.typename=='range' else (1<<self._range_stop)-1
    @property
    def _range_stop(self):return (1<<len(self.start))+self.width-1
    def __init__(self,key,context):
        width = context.width if context.length<=1 else context.length
        if isinstance(key,(int,ASTNode)):
            if isinstance(key,int) or key.typename=='const':
                self.typename = 'range'
                self.start = repair_const_type(int(key),width,0)
                self.stop  = self.start+1
                self.width = 1
            elif isinstance(key,Index):
                self.start = key.start
                self.stop  = key.stop
                self.width = key.width
                self.typename = key.typename
            elif isinstance(key,Expr):
                self.width = 1
                self.typename = '+:'
                self.start = key
                self.stop  = None
            else:e_unhandled_type(key.typename)
        elif isinstance(key,slice):
            if key.step is None:
                #[start:stop]
                self.typename = 'range'
                self.start = check_const_repair(0     if key.start is None else key.start,width,0)
                self.stop  = check_const_repair(width if key.stop  is None else key.stop ,width,1)
                self.width = self.stop - self.start
            else:
                if (key.start is None) == (key.stop is None):raise KeyError('Invalid indexing format.')
                self.width = check_const_type(key.step)
                #[start::width] -> [start+:width]
                #[:stop:width] -> [stop-:width]
                loc = key.stop if key.start is None else key.start
                if is_const_type(loc):
                    self.typename = 'range'
                    if key.start is None:
                        self.stop  = repair_const_type(int(key.stop),width,1)
                        self.start = self.stop  - self.width
                    else:
                        self.start = repair_const_type(int(loc),width,0)
                        self.stop  = self.start + self.width
                elif isinstance(loc,Expr):
                    self.typename = '-:' if key.start is None else '+:'
                    self.start = start
                    self.stop  = None
                else:e_unhandled_type(loc)
            if self.width< 0:raise IndexError('Invalid range with negative width.')    
            if self.width==0:raise IndexError('Invalid range with zero-width.')
        else:e_unhandled_type(key)
        if context.length>1 and len(self)!=1:raise TypeError('Invalid "[]" expr, %s[%s]'%(str(context),str(self)))
    def _generate(self,indent=0,p_precedence=99):
        if self.typename=='range':
            if self.width==1:return [['','',str(self.start)]]
            else:return [[str(self.stop-1),':',str(self.start)]]
        else:
            if self.width==1:return self.start._generate(indent)
            else:
                contents = self.start._generate(indent)
                contents[-1].append(self.typename)
                contents[-1].append(self.width)
                return contents
    __str__ = Expr.__str__
    def __len__(self):
        return self.width
    def __hash__(self):
        return 17*self.width+23*hash(str(self.start))+31*hash(str(self.stop))
    def __eq__(self,other):
        if not isinstance(other,Index):return False
        else:return self.start==other.start and self.stop==other.stop and self.width==other.width
class Fetch(BinaryOperator):
    @property
    def rhs(self):return self.childs[0]
    @rhs.setter
    def rhs(self,rhs):
        assert isinstance(rhs,Index)
        self.childs[0] = rhs
    def __init__(self,lhs,rhs):
        self._set_default('[]',n_childs=2)
        assert isinstance(lhs,Wire) or isinstance(lhs,Fetch) and lhs.lhs.length>1
        self.lhs = lhs
        self.rhs = rhs if isinstance(rhs,Index) else Index(rhs,lhs)
        self._calc_width()
    def __int__(self):
        if isinstance(self.lhs.value,list):return self.lhs.value[int(self.rhs.start)]
        else:return (int(self.lhs)>>int(self.rhs.start))&((1<<len(self.rhs))-1)
    def _fuse_range(self,key):
        base = self.rhs
        plus = Index(key,self)
        if not isinstance(base,Index) or not isinstance(plus,Index):
            raise TypeError('Implementation Error.')
        if base.typename != 'range' and plus.typename != 'range':
            raise TypeError('Invalid Composition of slicing "%s[%s]".'%(str(self),str(key)))
        return slice(base.start+plus.start,base.start+plus.stop)
    def __getitem__(self,key):
        if self.lhs.length>1:return Fetch(self,key)
        else:return self.lhs[self._fuse_range(key)]
    _wrap_value = Wire._wrap_value
    def __setitem__(self,key,val):
        if isinstance(self.lhs,Wire) and self.lhs.length==1:self.lhs[self._fuse_range(key)] = val
        accessing = self[key]
        target = accessing.lhs.lhs
        index  = accessing.lhs.rhs
        area   = accessing.rhs
        if target._typename == 'wire' and (index.typename != 'range' or area.typename != 'range'):
            raise ValueError('Assigning wire "%s" with non-constant index.'%str(self))
        self._wrap_value(val,len(area))
        target._mark_driven(area._range_mask)
        target.assignments.append(((index,area),val))
    def _mark_driven(self):
        if isinstance(self.lhs,Wire):self.lhs._mark_driven(self.rhs._range_mask)
        else:self.lhs.lhs._mark_driven(self.rhs._range_mask)
    def _get_target(self):
        if self.lhs._typename == '[]':return self.lhs.lhs
        else:return self.lhs