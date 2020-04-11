from pyvmodule.develope import *
__all__ = ['DataLine','ZeroLine','PipeLine','KeepBuffer']
class XLine(VStruct):
    '''
    expected:
    _infos :a list of variables' names and widths, e.g. [(<name>,<width>),...]
    optional:
    _shared:a set of variables' names that variables shared their value.
    _properties:a dict that map names to the function which generates the  values.
    
    functions defined as "regenerate_xxx(t,s,idx)":
    Shows "xxx" is a name of variable which need to regenerate its value with index.
    the function is called instead of using assignment "t[:] = s".
    '''
    _properties = dict()
    _shared = set()
    _regenerate = set()
    @property
    def width(self):return self._width
    @property
    def align(self):return self._align
    @property
    def way_num(self):return self._way_num
    @property
    def data_num(self):return self.way_num<<self.align
    def __init__(self,align=0,way_num=1,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self._properties_finished = set()
        self._align = align
        self._way_num = way_num
        self._io = io
        self._init(align=align,way_num=way_num,io=io,**kwargs)
        self._init_end()
    def _init(self,**kwargs):
        '''
        override this function to define "_infos" dynamically.
        '''
        pass
    @classmethod
    def detect_regenerate(cls):
        regen = set()
        for name in vars(cls):
            if name.startswith('regenerate_'):regen.add(name[len('regenerate_'):])
        cls._regenerate = regen
    @property
    def entry(self):
        e = Wire(self._width)
        self.assigns(e)
        return e
    @property
    def entry_width(self):return self._width
    def assigns(self,e):
        base = 0
        for name,width in self._infos:
            w = getattr(self,name)
            e[base::len(w)] = w
            base += len(w)
    def __getattr__(self,name):
        if name in self._properties:
            if name in self._properties_finished:raise AttributeError('Self Looping Property: %s' % name)
            self._properties_finished.add(name)
            setattr(self,name,Wire(self._properties[name](self)))
            self._properties_finished.clear()
            return getattr(self,name)
        else:raise AttributeError('Unknown attribute : %s' % name)
class DataLine(XLine):
    def _init_end(self):
        self._width = 0
        tasks = []
        for name,width in self._infos:
            if name not in self._shared:width*=self.data_num
            setattr(self,name,Wire(width,io=self._io))
            self._width += width
            task = self._properties.get(name,None)
            if not task is None:tasks.append((name,task))
        for name,task in tasks:
            getattr(self,name)[:] = task(self)
    def assigned_with(self,e):
        base = 0
        for name,width in self._infos:
            w = getattr(self,name)
            w[:] = e[base::len(w)]
            base += len(w)
    def pickout(self,idx,io=None,**kwargs):
        pick = type(self)(io=io,**kwargs)
        for name,width in pick._infos:
            s = getattr(self,name)
            t = getattr(pick,name)
            s = s if name in self._shared else s[width*idx::width]
            if name not in self._regenerate:t[:] = s
            else:getattr(self,'regenerate_'+name)(t,s,idx)
        return pick
    def collects(self,idx,pick):
        for name,width in self._infos:
            if not hasattr(pick,name):continue
            s = getattr(self,name)
            t = getattr(pick,name)
            if idx is None:s[:] = t
            elif name in self._shared:
                if idx==0:s[:] = t
            else:s[width*idx::width] = t
class ZeroLine(DataLine):
    _infos = []
    def __getattr__(self,name):return 0
Zero = ZeroLine()
class PipeLine(XLine):
    def _init_end(self):
        self._width = 0
        for name,width in self._infos:
            if name not in self._shared:width*=self.data_num
            setattr(self,name,Reg(width,io=self._io))
            self._width += width
    def pipelining(self,cur,pick,idx=None):
        for name,width in self._infos:
            if not hasattr(pick,name):continue
            s = getattr(self,name)
            t = getattr(pick,name)
            if idx is None:cur[s:t]
            elif name in self._shared:
                if idx==0:cur[s:t]
            else:cur[s[width*idx::width]:t]
    def captures(self,conds=None,values=None,reset=None,init=Zero,otherwise=None,prev=None):
        w = prev
        if not reset is None:
            w = When(reset) if w is None else w.When(reset)
            self.pipelining(w,init)
        if isinstance(conds,list):
            assert len(conds)==len(values)
            for i in range(len(conds)):
                cond = conds[i]
                w = When(cond) if w is None else w.When(cond)
                self.pipelining(w,values[i])
        elif not conds is None:
            assert not values is None
            w = When(conds) if w is None else w.When(conds)
            self.pipelining(w,values)
        if not otherwise is None:
            w = w.Otherwise
            self.pipelining(w,otherwise)
