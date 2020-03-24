__all__ = ['NamingNode','NamingDict','NamingRoot','a_name_valid']
from .ast import ASTNode
import warnings
def raise_error(err):raise err
keywords = {'begin','end','always','initial','generate','endgenerate','if','else','for',
    'genvar','integer','wire','reg','module','endmodule','input','output','inout','assign','case','endcase','force'}
def a_name_type(name):return isinstance(name,str) or raise_error(NameError('Type of name must be type "str", not "%s".'       %(type(name))))
def a_name_len (name):return len(name)<=32        or raise_error(NameError('Name "%s" is too long.(longer than %d characters)'%(name,32)))
def a_name_start_alpha(name):return name[ 0].isalpha() or raise_error(NameError('Name "%s" must not start with "%s".'%(name,name[ 0])))
def a_name_end_alnum  (name):return name[-1].isalnum() or raise_error(NameError('Name "%s" must not end with "%s".'  %(name,name[-1])))
def a_name_end_alpha  (name):return name[-1].isalpha() or raise_error(NameError('Name "%s" must not end with "%s".'  %(name,name[-1])))
def a_name_identifier (name):return name.isidentifier() or raise_error(NameError('Name should be an identifier, "%s" has invalid characters.'  %(name)))
def a_name_underline  (name):return '__' not in name    or raise_error(NameError('"_" must not be consecutive for name "%s".'%(name)))
def a_name_not_keyword(name):return name not in keywords or raise_error(NameError('Name must not be keyword "%s".'%(name)))
def a_name_basic(name):return a_name_type(name) and a_name_identifier(name) and a_name_len(name) and a_name_start_alpha(name) and a_name_underline(name) and a_name_not_keyword(name)
def a_name_valid    (name):return a_name_basic(name) and a_name_end_alnum(name)
def a_name_valid_ssa(name):return a_name_basic(name) and a_name_end_alpha(name)
def a_ssa_list_free(name,ssa):return name+'s' not in ssa or raise_error(NameError('name "%ss" conflicts with previos SSA name "%s".'%(name,name)))
def a_ssa_name_free(name,ssa):return name[-1]!='s' or name[:-1] not in ssa or raise_error(NameError('Name "%s" conflicts with previos SSA name "%ss".'%(name,name)))
def a_ssa_no_alias (name,ssa):return a_ssa_list_free(name,ssa) and a_ssa_name_free(name,ssa)
def a_name_once(name,naming,val=None):return name not in naming or naming[name] is val or raise_error(KeyError('Redefining object "%s".'%name))
def a_name_no_alias(name,var,ssa,val=None):a_name_once(name,var,val) and a_name_once(name,ssa,val) and a_ssa_no_alias(name,ssa)
def new_anonymous_name(self,val=[0]):
    val[0] += 1
    return 'temp_%d'%val[0]
def naming_setattr(getval,setval):
    def _naming_setattr(self,key,val):
        if key[0]=='_':return setval(self,key,val)
        if key in self._naming_ssa:
            ssa_list = getval(self,key+'s')
            setval(self,key,val)
            key = key+str(len(ssa_list))
            ssa_list.append(val)
        naming = self._naming_var
        a_name_once(key,naming,val)
        if isinstance(val,NamingNode):
            naming_parent(val,self,key)
        setval(self,key,val)
    return _naming_setattr
def naming_grow(p,pname,c,cname):
    if not c._mounting or p._bypass:return cname
    if p._reverse:return '%s_%s'%(cname,pname)
    else:return '%s_%s'%(pname,cname)
def naming_ancestors(self,tail=False):
    node = self._naming_parent
    while isinstance(node,NamingNode):
        yield node
        node = node._naming_parent
    if node is None:return
    if tail:yield node
def naming_extract(self,prev):
    next = self._ins_name
    nodes = [self]
    new_names = [next]
    for name,node in self._naming_var.items():
        nodes.append(node)
        new_names.append(naming_grow(self,next,node,name))
    if not prev is None:old_names = [prev]+[naming_grow(self,prev,node,name) for name,node in self._naming_var.items()]
    else:old_names = []
    return nodes,new_names,old_names
def naming_anonymous_name(self):
    if not hasattr(self,'_anonymous_name_value'):self._anonymous_name_value = new_anonymous_name(self)
    return self._anonymous_name_value
def naming_consistency_maintaining(self,prev=None):
    if self._naming_parent is None:return
    if self._ins_name==prev:return
    nodes,new_names,old_names = naming_extract(self,prev)
    for ancestor in naming_ancestors(self,tail=True):
        for i in range(len(old_names)):
            del ancestor._naming_var[old_names[i]]
        for i in range(len(new_names)):
            new_name = new_names[i]
            a_name_no_alias(new_name,ancestor._naming_var,ancestor._naming_ssa,nodes[i])
            ancestor._naming_var[new_name] = nodes[i]
            ancestor._setattr_(new_name,nodes[i])
        if not isinstance(ancestor,NamingNode):continue
        for i in range(len(new_names)):
            new_names[i] = naming_grow(ancestor,ancestor._ins_name,nodes[i],new_names[i])
        for i in range(len(old_names)):
            old_names[i] = naming_grow(ancestor,ancestor._ins_name,nodes[i],old_names[i])
    return
def naming_form_name(self):
    if self._naming_nameless:warnings.warn('Nameless object reference detected .')
    if self._ins_name is None:self._ins_name = naming_anonymous_name(self)
    if not self._mounting:return self._ins_name
    parts = [self._ins_name]
    for ancestor in naming_ancestors(self):
        if ancestor._bypass:continue
        if ancestor._ins_name is None:continue
        if ancestor._reverse:parts.append(ancestor._ins_name)
        else:parts.insert(0,ancestor._ins_name)
    return '_'.join(parts)
def naming_root(self):
    while isinstance(self._naming_root._naming_parent,NamingNode):
        self._naming_root = self._naming_root._naming_parent
    if self._naming_root._naming_parent is None:return self._naming_root
    else:return self._naming_root._naming_parent
def naming_parent(self,parent,key):
    if parent is self:return
    if isinstance(parent,NamingNode):
        skip = not self._naming_parent is None
        if not skip:
            for ancestor in naming_ancestors(parent):
                if ancestor is self:
                    skip = True
                    break
        if not skip:
            if self._naming_nameless:self.ins_name = key
            self._naming_parent = parent
            naming_consistency_maintaining(self)
        else:
            if isinstance(type(parent),NamingRoot):
                for name,val in self._naming_var.items():
                    setattr(parent,'%s_%s'%(key,name),val)
    else:
        if not isinstance(parent,(NamingDict,NamingRoot)):raise TypeError('Invalid parent type.')
        if self._naming_nameless:
            self.ins_name = key
        root = naming_root(self)
        if isinstance(root,NamingNode):
            root._naming_parent = parent
            naming_consistency_maintaining(root)
            return
        elif parent is root:return
        else:raise ReferenceError('Cross module reference.')
class NamingNode(ASTNode):
    @property
    def ins_name(self):return naming_form_name(self)
    @ins_name.setter
    def ins_name(self,name):
        if name is None:return
        if isinstance(name,str):
            a_name_valid(name)
            name_update = self._ins_name
            self._ins_name = name
            self._naming_nameless = False
            naming_consistency_maintaining(self,name_update)
        else:raise TypeError('Name should be a "str", not "%s".'%type(name))
    @property
    def name(self):return self.ins_name
    @name.setter
    def name(self,name):self.ins_name = name
    def enable_ssa(self,name):
        a_name_no_alias(name,self._naming_var,self._naming_ssa)
        self._naming_ssa.add(name)
        setattr(self,name+'s',[])
    def __init__(self,name=None,reverse=False,bypass=False,mounting=True,**kwargs):
        self._naming_ssa = set()
        self._naming_var = {}
        self._naming_parent = None
        self._naming_nameless = name is None
        self._ins_name = None
        if not self._naming_nameless:self.ins_name = name
        self._naming_root = self
        self._bypass = bypass
        self._mounting = mounting
        self._reverse = reverse
    def __str__(self):return self.name
    @property
    def _parent(self):return self._parent_node
    __setattr__ = naming_setattr(getattr,object.__setattr__)
    def __iter__(self):
        for name,val in self._naming_var.items():yield val
    _setattr_ = object.__setattr__
class NamingDict(dict):
    @property
    def _naming_ssa(self):return self['_naming_ssa']
    @property
    def _naming_var(self):return self['_naming_var']
    __setitem__ = naming_setattr(dict.__getitem__,dict.__setitem__)
    def __init__(self,prev):
        self['_naming_ssa'] = set()  if '_naming_ssa' not in prev else prev['_naming_ssa']
        self['_naming_var'] = dict() if '_naming_var' not in prev else prev['_naming_var']
    def enable_ssa(self,name):
        a_name_no_alias(name,self._naming_var,self._naming_ssa)
        self._naming_ssa.add(name)
        self[name+'s'] = []
    _setattr_ = dict.__setitem__
class NamingRoot(type):
    enable_ssa = NamingNode.enable_ssa
    _setattr_ = type.__setattr__
    __setattr__ = naming_setattr(getattr,type.__setattr__)
def ports(x):
    for name,var in x._naming_var.items():
        if var.typename in {'wire','reg'} and not var.io is None:yield var