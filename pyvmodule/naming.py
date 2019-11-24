__all__ = ['NamingNode','NamingDict','NamingRoot']
class NamingNode:
    anonymous_object_id = 0
    @classmethod
    def _pop_anonymous_object_id(self):
        self.anonymous_object_id += 1
        return self.anonymous_object_id
    def _get_name(self,end=None):
        if not self._mounting or self._scope==None:
            return self.partial_name
        scope = self._scope
        prefix = []
        suffix = []
        while scope!=None and not scope is end and isinstance(scope,NamingNode):
            if not scope._bypass:
                name = scope.partial_name
                if scope._reverse:
                    suffix.append(name)
                else:
                    prefix.insert(0,name)
            scope = scope._scope
        parts = prefix+[self.partial_name]+suffix
        return '_'.join(parts)
    def _get_root(self):
        scope = self
        while scope!=None and isinstance(scope,NamingNode):
            scope = scope._scope
        return scope
    def __str__(self):
        return self.name
    def __init__(self,name=None,reverse=False,bypass=False,mounting=True):
        if name!=None and not isinstance(name,str):raise TypeError('Name should be str.') 
        self._scope = None
        self._nameless = name==None
        self._root = None
        self.name = name if name!=None else 'temp_%d'%self._pop_anonymous_object_id()
        self._childs = []
        self._bypass = bypass
        self._mounting = mounting
        self._reverse = reverse
    def __setattr__(self,key,val):
        if val is self:raise ValueError('Self-looping.')
        if key=='name' and not isinstance(val,str):
            raise TypeError('Name should be a "str", not "%s".'%str(type(val)))
        if key[0]!='_' and isinstance(val,NamingNode):
            self._childs.append(val)
            if val._nameless:
                val.name = key
                val._nameless = False
            if val._scope==None:
                val._scope = self
            if self._root!=None:
                if val._root!=None and not val._root is self._root:raise RuntimeError('Cross module reference.')
                if val._root==None:
                    val._root = self._root
                    self._root._receive(val)
        object.__setattr__(self,key,val)
    def __getattribute__(self,key):
        if key=='name':
            name = self._get_name()
            return name
        if key=='partial_name':
            return object.__getattribute__(self,'name')
        return object.__getattribute__(self,key)
    def __hash__(self):
        return hash(self.name)
    def __eq__(self,other):
        return self is other
    def __iter__(self):
        for val in self._childs:
            if not isinstance(val,NamingNode):
                continue
            yield val
            if val._scope is self:
                for subval in val:yield subval
        return
class NamingCheck:
    wire_keywords = {'name','comments','io','assignments','typename','width'}
    def check_type(key,val,typed_keywords={'name':(str,type(None)),'ip_only':bool}):
        if key in typed_keywords and not isinstance(val,typed_keywords[key]):
            raise TypeError(key+' should be a "%s", not "%s".'%(str(typed_keywords[key]),str(type(val))))
    def check_writable(key,read_only_objects={'save','regist','auto_connect','comments','mydict'}):
        if key in read_only_objects:
            raise KeyError('Cannot overwrites built-in object "%s".'%key)
    def check_redef(key,val,other,definition_types={'wire','reg','module'}):
        if not hasattr(other,'typename') or other.typename not in definition_types:
            return
        if other.name == key and not val is other:
            raise KeyError('Redefining "%s" object "%s".'%(other.typename,key))
    def collect_subscope(self,val):
        if not val._root is self:
            for subval in val:
                self._receive(subval)
            val._root = self
class NamingDict(dict):
    def _receive(self,val):
        name = val.name
        if name in self:
            if not self[name] is val:
                raise KeyError('Redefined "%s" object "%s".'%(str(type(val)),name))
        else:
            self[name] = val
        for child in val._childs:
            self._receive(child)
    def __setitem__(self,key,val):
        if key in self:
            NamingCheck.check_writable(key)
            NamingCheck.check_redef(key,val,self[key])
        NamingCheck.check_type(key,val)
        dict.__setitem__(self,key,val)
        if isinstance(val,list):
            for subval in val:
                if isinstance(subval,NamingNode):
                    self._receive(subval)
        if not isinstance(val,NamingNode):return
        if val._nameless:
            val.name = key
            val._nameless = False
        if val._scope==None:
            val._scope = self
        name = val.name
        if name!=key and name in self:NamingCheck.check_redef(name,val,self[name])
        dict.__setitem__(self,name,val)
        NamingCheck.collect_subscope(self,val)
    def __getitem__(self,key):
        return dict.__getitem__(self,key)
class NamingRoot(type):
    def _receive(self,val):
        name = val.name
        if hasattr(self,name):
            if not getattr(self,name) is val:
                raise KeyError('Redefined "%s" object "%s".'%(str(type(val)),name))
        else:
            setattr(self,val.name,val)
        for child in val._childs:
            self._receive(child)
    def __setattr__(self,key,val):
        if key in self.__dict__:
            NamingCheck.check_writable(key)
            NamingCheck.check_redef(key,val,self.__dict__[key])
        NamingCheck.check_type(key,val)
        type.__setattr__(self,key,val)
        if isinstance(val,list):
            for subval in val:
                if isinstance(subval,NamingNode):
                    self._receive(subval)
        if not isinstance(val,NamingNode):return
        if val._nameless:
            val.name = key
            val._nameless = False
        if val._scope==None:
            val._scope = self
        name = val.name
        if name!=key and name in self.__dict__:NamingCheck.check_redef(name,val,self.__dict__[name])
        type.__setattr__(self,name,val)
        NamingCheck.collect_subscope(self,val)
    def __getattribute__(self,key):
        return type.__getattribute__(self,key)
        