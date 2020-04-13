import sys
from .expr import wrap_expr
from .wire import Wire
from .ast import ASTNode
from .naming import NamingDict,NamingRoot,NamingNode
from .compute.auto_connect import prepare_auto_connect
from .compute.copy import meta_copy
from .ctrlblk import ControlBlock,Initial
import warnings
__all__ = ['VModule','VModuleMeta','VModuleHelper']
def name_getter(self,key):return self['_mod_name']
def ip_only_getter(self,key):return self['_ip_only']
def mydict_getter(self,key):return self
def auto_connect_getter(self,key):return self['_auto_connect']
def name_setter(self,key,val):
    if not val.isidentifier():raise NameError('Invalid name "%s"'%val)
    self['_mod_name'] = val
def ip_only_setter(self,key,val):
    if not isinstance(val,bool):raise TypeError('Type of "ip_only" should be bool.')
    self['_ip_only'] = val
def forbid_setter(self,key,val):raise NameError('Cannot overwrite property "key".')
_getter = {
    'name'    :name_getter,
    'mod_name':name_getter,
    'ip_only' :ip_only_getter,
    'mydict'  :mydict_getter,
    'auto_connect':auto_connect_getter}
_setter = {
    'name'    :name_setter,
    'mod_name':name_setter,
    'ip_only' :ip_only_setter,
    'mydict'  :forbid_setter,
    'auto_connect':forbid_setter}
class VModuleMetaDict(NamingDict):
    def __getitem__(self,key):return _getter.get(key,NamingDict.__getitem__)(self,key)
    def __setitem__(self,key,val):return _setter.get(key,NamingDict.__setitem__)(self,key,val)
    def __init__(self,name,prev):
        assert not name is None
        NamingDict.__init__(self,prev)
        if 'ip_only'   not in prev:self['ip_only'  ] = False
        for key,val in prev.items():mydict[key] = val
        if 'comments'  in self:self['comments'] = self['comments'].copy()
        else:self['comments' ] = []
        if 'copyright' in self:self['copyright'] = self['copyright'].copy()
        else:self['copyright'] = []
        self['_auto_connect'] = prepare_auto_connect(self,isdict=True)
        self['name'] = name
class VModuleMeta(NamingRoot):
    _auto_port = True
    @property
    def name(self):return self._mod_name
    @name.setter
    def name(self,name):self.mod_name = name
    @property
    def mod_name(self):return self._mod_name
    @mod_name.setter
    def mod_name(self,val):
        if not val.isidentifier():raise NameError('Invalid name "%s"'%val)
        self._mod_name = val
    @property
    def ip_only(self):return self._ip_only
    @ip_only.setter
    def ip_only(self,val):
        if not isinstance(val,bool):raise TypeError('Type of "ip_only" should be bool.')
        self._ip_only = val
    @property
    def auto_port(self):return VModuleMeta._auto_port
    @auto_port.setter
    def auto_port(self,enable):
        if not isinstance(enable,bool):raise TypeError(enable)
        VModuleMeta._auto_port = enable
    @property
    def mydict(self):return self.__dict__
    @property
    def auto_connect(self):return self._auto_connect
    @staticmethod
    def __new__(meta,name,bases,attrs):
        cls = type.__new__(meta,name,bases,attrs)
        for key,val in cls.mydict.items():
            if isinstance(val,NamingNode) and not isinstance(val._naming_parent,NamingNode):
                val._naming_parent = cls
        cls._auto_connect = staticmethod(prepare_auto_connect(cls,isdict=False))
        return cls
    @classmethod
    def __prepare__(meta,name,bases):
        prev = type.__prepare__(meta,name,bases)
        mydict = VModuleMetaDict(name,prev)
        meta_copy(mydict,bases)
        return mydict
    @property
    def typename(self):return 'module'
    @property
    def language(self):return ASTNode._language
    @language.setter
    def language(self,language):ASTNode.set_language(language)
    def __str__(self):return str(VModuleHelper(self))

class VModuleHelper:
    @property
    def name(self):return self.module.name
    def check_case_sensitivity(self):
        names = {}
        for name in self.names:
            lower_name = name.lower()
            if lower_name in names:raise NameError('Name "%s" and "%s" are conflicting when case sensitivity is disabled.'%(pre.ins_name,val.ins_name))
            names[lower_name] = name
    def __str__(self):return self.code
    @staticmethod
    def auto_port(items):
        for name,var in items:
            if not isinstance(var,Wire):continue
            var._auto_port_determined()
    def __init__(self,obj,prefix=None,copyright=None,**kwargs):
        if not prefix is None:obj.mod_name = prefix+'_'+obj.mod_name
        if not copyright is None:obj.copyright.append(copyright)
        self.module = obj
        self.names = obj._naming_var.copy()
        if kwargs.get('enable_case_sensitivity',False):self.check_case_sensitivity()
        self.auto_port(self.names.items())
        if hasattr(self.module,'clock'):
            self.clock = getattr(self.module,'clock')
        else:
            self.clock = None
        self.extract()
    @property
    def code(self):
        if hasattr(self,'_code'):return self._code
        else:
            self._code = self.gen()
            return self._code
    def extract(self):
        self.rams = []
        self.ports = []
        self.inner_signals = []
        self.wires = []
        self.modules = []
        self.registers = [] 
        self.controlblocks = {}
        for name,node in self.names.items():
            for obj in node._naming_recv:
                if isinstance(obj,ControlBlock):
                    if isinstance(obj,Initial):self.controlblocks[id(obj)] = obj
                else:raise TypeError(obj)
            if node.typename=='struct':continue
            getattr(self,'extract_'+node.typename)(node)
    def extract_module(self,node):
        self.modules.append(node)
    def extract_wire(self,node):
        if node.io is None:self.inner_signals.append(node)
        else:self.ports.append(node)
        self.wires.append(node)
    def extract_reg(self,node):
        if not node.io is None:self.ports.append(node)
        elif node.length>1:self.rams.append(node)
        else:self.inner_signals.append(node)
        self.registers.append(node)
        if node.clock is None:node.clock = self.clock
        node._refresh_controlblocks()
        for blk in node.controlblocks:
            self.controlblocks[id(blk)] = blk
    def gen(self,*args,**kwargs):return ASTNode._meta_generate(self,*args,**kwargs)
from .vcircuit import VCircuit
class VModule(NamingNode,metaclass=VModuleMeta):
    def _setattr_(self,key,val):
        p = type(self)._naming_var.get(key,None) if key[0]!='_' else None
        if isinstance(p,Wire) and not p.io is None:
            if self.__dict__.get(key,None) is val:return
            val = wrap_expr(val)
            val._connect_port(self,p)
        object.__setattr__(self,key,val)
    def __getattr__(self,key):
        p = type(self)._naming_var.get(key,None) if key[0]!='_' else None
        if p is None:raise NameError('Name "%s" does not exist '%key)
        v = p._node_clone()
        setattr(self,key,v)
        return v
    def __init__(self,**kwargs):
        NamingNode.__init__(self,**kwargs)
        self.comments = []
        self.typename = 'module'
        for key,val in kwargs.items():
            if isinstance(val,NamingNode):
                setattr(self,key,val)
    @classmethod
    def save(cls,**kwargs):VCircuit(cls,**kwargs).save(**kwargs)
    def _generate(self,*args,**kwargs):return self._inst_generate(*args,**kwargs)
    def _node_clone(self):return type(self)()
