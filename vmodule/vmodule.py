#----------------------------------------------------------------------
#pyvmodule:vmodule.py
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
__all__ = ['VModule']
from .expr import *
from .ast import ASTNode
from .check import VChecker
from .codegen import code_generators
from .vstruct import set_components
from .vstruct import VStruct
import warnings

def meta_check_item(thedict,key,val):
    if key in VModuleMetaDict.keywords:
        if key in VModuleMetaDict.read_only_objects:
            if key in thedict:
                raise KeyError('Cannot overwrites built-in object "%s".'%key)
        elif key in {'_name'}:
            if val!=None and not isinstance(val,str):
                raise TypeError('name should be a "str".')
        elif key in {'ip_only'}:
            if not isinstance(val,bool):
                raise TypeError('"%s" should be a "bool".'%key)
    elif key in thedict:
        other = thedict[key]
        if isinstance(other,ASTNode) and other.typename in {'wire','reg','module'}:
            if other.name == key:
                raise KeyError('Redefining %s object "%s".'%(other.typename,key))
def meta_set_more_attr(obj,key,val):
    if isinstance(val,ASTNode):
        if val.typename in {'wire','reg','module'}:
            if val._name == None:
                val._name = VChecker.identifier(key)
            val_name = val.name
            if val_name != key:
                if hasattr(obj,val_name):
                    if not getattr(obj,val_name) is val:
                        if isinstance(val,Wire):
                            raise KeyError('Redefined wire "%s".'%val_name)
                        else:
                            warnings.warn('Wire "%s" within "%s" masked %s variable.'%(val_name,key,type(getattr(obj,val_name))))
                type.__setattr__(obj,val_name,val)
    elif isinstance(val,list):
        for subval in val:
            meta_set_more_attr(obj,key,subval)
    elif isinstance(val,VStruct):
        if val._name == None:
            val._name = key
        for subval in val:
            meta_set_more_attr(obj,key,subval)
def meta_set_more_item(thedict,key,val):
    if isinstance(val,ASTNode):
        if val.typename in {'wire','reg','module'}:
            if val._name == None:
                val._name = VChecker.identifier(key)
            val_name = val.name
            if val_name != key:
                if val_name in thedict:
                    if not thedict[val_name] is val:
                        if isinstance(val,Wire):
                            raise KeyError('Redefined wire "%s".'%val_name)
                        else:
                            warnings.warn('Wire "%s" within "%s" masked %s variable.'%(val_name,key,type(thedict[val_name])))
                dict.__setitem__(thedict,val_name,val)
    elif isinstance(val,list):
        for subval in val:
            meta_set_more_item(thedict,key,subval)
    elif isinstance(val,VStruct):
        if val._name == None:
            val._name = key
        for subval in val:
            meta_set_more_item(thedict,key,subval)
class VModuleMetaDict(dict):
    read_only_objects = {'save','regist','auto_connect','comments','mydict'}
    keywords = read_only_objects|{'name','ip_only'}
    wire_keywords = {'name','comments','io','assignments','typename','width'}
    def __init__(self,name=None):
        assert name!=None
        self.extra_codes = []
        self['mydict'] = self
        self['_name'] = name
        self['comments'] = []
        self['copyright'] = []
    def __setitem__(self,key,val):
        if key=='name':
            if 'name' in self:
                if not isinstance(val,str):
                    raise TypeError('name must be str')
                return dict.__setitem__(self,'_name',val)
            else:
                return dict.__setitem__(self,'name',val)
                
        meta_check_item(self,key,val)
        meta_set_more_item(self,key,val)
        dict.__setitem__(self,key,val)
def get_magic_methods(mydict):
    def get_match_table(obj,pattern,io):
        if pattern.count('*')>1:
            raise ValueError('Too many "*" to match.')
        index = pattern.find('*')
        if index<0:
            if pattern not in obj.mydict:
                return {}
            val = obj.mydict[pattern]
            if not isinstance(val,Wire) or val.io==None:
                return {}
            if io!=None and val.io!=io:
                return {}
            return {'':pattern}
        else:
            table = {}
            lhs = pattern[:index]
            rhs = pattern[index+1:]
            length = len(lhs)+len(rhs)
            for val in obj.ports():
                val_name = val.name
                if val_name in obj.__dict__:
                    continue
                if len(val_name)<length:
                    continue
                if lhs!=val_name[:len(lhs)]:
                    continue
                if rhs!=val_name[len(val_name)-len(rhs):]:
                    continue
                if io!=None and val.io!=io:
                    continue
                core = val_name[len(lhs):len(val_name)-len(rhs)]
                table[core] = val_name
            return table
    def auto_connect(*objs,name='+',dual={},io=None):
        if len(objs)<=0:
            raise TypeError('Too few arguments for "auto_connect".')
        if name.count('*')+name.count('+')>1:
            raise ValueError('Too many "*" or "+" in name pattern "%s".'%name)
        # auto_connect(<Wire>,...)
        if isinstance(objs[0],Wire):
            for obj in objs:
                if not isinstance(obj,Wire):
                    raise TypeError('Unrecognized auto-connection requirement.')
                if not hasattr(obj,'components'):
                    raise KeyError('Missing declaration of "components"')
                
                thestruct = VStruct(obj.components)
                thestruct._scope = obj
                if obj.io == 'input':
                    Concatenate(list(thestruct))[:] = obj
                elif obj.io == 'output':
                    obj[:] = Concatenate(list(thestruct))
                else:
                    raise KeyError('Failed to resolve auto-connection.')
                    
                for key in thestruct.__dict__:
                    component = thestruct.__dict__
                    if isinstance(component,(Wire,VStruct)):
                        component._scope = obj
                        setattr(obj,key,component)
                    if isinstance(component,Wire):
                        cname = component.name
                        if cname not in mydict:
                            mydict[cname] = component
                            continue
                        if not component is mydict[cname]:
                            raise KeyError('Masked variable "%s".'%cname)
            return obj.components
        # auto_connect(<VModule>)
        # auto_connect(<VModule>,<str>)
        # auto_connect(<VModule>,<VModule>)
        # auto_connect(<VModule>,<VModule>,<str>)
        # auto_connect(<VModule>,<VModule>,<str>,<str>)
        if isinstance(objs[-1],(str,Wire)):
            tnames = [str(objs[-1])]
            objs = objs[:-1]
        elif isinstance(objs[-1],list):
            tnames = objs[-1]
            objs = objs[:-1]
        else:
            tnames = ['*']
        if len(objs)<=0:
            raise TypeError('Too few arguments for "auto_connect".')
        if isinstance(objs[-1],(str,Wire)):
            snames = [str(objs[-1])]
            objs = objs[:-1]
        elif isinstance(objs[-1],list):
            snames = [objs[-1]]
            objs = objs[:-1]
        else:
            snames = tnames
        if len(snames)!=len(tnames):
            raise TypeError('Unmatched connect list size.')
        if len(objs)<=0:
            raise TypeError('Too few arguments for "auto_connect".')
        if len(objs)>2:
            raise TypeError('Too many arguments for "auto_connect".')
        decl_list = []
        if len(objs)==1:
            obj = objs[0]
            if not snames is tnames:
                raise ValueError('Invalid format.')
            if isinstance(obj,VModule):
                for i in range(len(tnames)):
                    tname = tnames[i]
                    ttable = get_match_table(obj,tname,io)
                    for tcore in ttable:
                        tkey = ttable[tcore]
                        pkey = name
                        pkey = pkey.replace('*',tcore)
                        pkey = pkey.replace('+',tkey)
                        if pkey not in mydict:
                            pval = obj.mydict[tkey].copy()
                            pval._name = VChecker.identifier(pkey)
                            pval.io = VChecker.port(io,pval.length,pval.typename)
                            decl_list.append(pval)
                            mydict[pkey] = pval
                        elif not isinstance(mydict[pkey],Wire):
                            raise TypeError('"%s" variable "%s" in parent is not a wire.'%(type(mydict[pkey]),pkey))
                        else:
                            pval = mydict[pkey]
                        setattr(obj,tkey,pval)
                    if len(ttable)==0:
                        warnings.warn('No connections matches "%s" between module "%s" and parent.'%(tname,obj.name))
            else:
                VChecker.unhandled_type(obj)
            return decl_list
        if len(objs)==2:
            if isinstance(objs[0],VModule) and isinstance(objs[1],VModule):
                for i in range(len(tnames)):
                    tname = tnames[i]
                    sname = snames[i]
                    sobj = objs[0]
                    tobj = objs[1]
                    stable = get_match_table(sobj,sname,io)
                    ttable = get_match_table(tobj,tname,io)
                    hit_count = 0
                    for score in stable:
                        skey = stable[score]
                        if score in ttable:
                            hit_count+=1
                            if score in dual:
                                tcore = dual[score]
                            else:
                                tcore = score
                            tkey = ttable[tcore]
                            port_dual = {'input':'output','output':'input','inout':'inout'}
                            if port_dual[sobj.mydict[skey].io]!=tobj.mydict[tkey].io:
                                raise TypeError('Unmatched input-output port type, from %s of "%s" to %s of "%s"'%(skey,sobj.mydict[skey].io,tkey,tobj.mydict[tkey].io))
                            pkey = name
                            pkey = pkey.replace('*',score)
                            pkey = pkey.replace('+',skey)
                            if pkey not in mydict:
                                pval = sobj.mydict[skey].copy()
                                pval._name = VChecker.identifier(pkey)
                                pval.io = VChecker.port(io,pval.typename,pval.length)
                                decl_list.append(pval)
                                mydict[pkey] = pval
                            elif not isinstance(mydict[pkey],Wire):
                                raise TypeError('"%s" variable "%s" in parent is not a wire.'%(type(mydict[pkey]),pkey))
                            else:
                                pval = mydict[pkey]
                            setattr(sobj,skey,pval)
                            setattr(tobj,tkey,pval)
                        else:
                            warnings.warn('Matched wire "%s" is not declared in module "%s"'%(skey,tobj.name))
                    if hit_count<len(ttable):
                        for tcore in ttable:
                            if tcore not in stable:
                                tkey = ttable[tcore]
                                warnings.warn('Matched wire "%s" is not declared in module "%s"'%(tkey,sobj.name))
            else:
                VChecker.unhandled_type(objs[0])
            return decl_list
    def regist(obj,name='+'):
        if isinstance(obj,Wire) or isinstance(obj,VModule):
            target = name.replace('+',obj.name)
            if target in mydict and not obj is mydict[target]:
                raise KeyError('Redefining "%s".'%obj.name)
            if target!=obj.name and obj.name in mydict and obj is mydict[obj.name]:
                warnings.warn('Renaming existing object "%s", ignored.'%obj.name)
                return
            obj._name = VChecker.identifier(target)
            mydict[obj.name] = obj
            if isinstance(obj,VModule):
                for key in obj.__dict__:
                    val = obj.__dict__[key]
                    if isinstance(val,Wire):
                        regist(val)
        elif isinstance(obj,list):
            for w in obj:
                regist(w,name=name)
        elif isinstance(obj,dict):
            for k,w in obj.items():
                regist(w,name=name)
        elif isinstance(obj,str):
            mydict.extra_codes.append(obj)
        elif isinstance(obj,type(None)):
            return
        else:
            VChecker.unhandled_type(obj)
    return regist,auto_connect
class VModuleMeta(type):
    _global_ip_name = ''
    @staticmethod
    def __new__(meta,name,bases,attrs):
        cls = type.__new__(meta,name,bases,attrs)
        type.__setattr__(cls,'mydict',cls.__dict__)
        regist,auto_connect = get_magic_methods(cls.mydict)
        type.__setattr__(cls,'regist',regist)
        type.__setattr__(cls,'auto_connect',auto_connect)
        return cls
    @classmethod
    def __prepare__(meta,name,bases):
        mydict = VModuleMetaDict(name)
        ext = False
        for base in bases:
            if isinstance(base,VModuleMeta):
                ext = True
                for key,val in base.mydict.items():
                    dict.__setitem__(mydict,key,val)
                dict.__setitem__(mydict,'mydict',mydict)
                dict.__setitem__(mydict,'_name',name)
                break
        dict.__setitem__(mydict,'_ip_name',meta._global_ip_name)
        regist,auto_connect = get_magic_methods(mydict)
        if 'comments' not in mydict:
            dict.__setitem__(mydict,'comments',[])
        else:
            dict.__setitem__(mydict,'comments',mydict['comments'].copy())
        dict.__setitem__(mydict,'regist',regist)
        dict.__setitem__(mydict,'auto_connect',auto_connect)
        return mydict
    @property
    def name(self):
        if self._ip_name!='':
            return self._ip_name+'_'+self._name
        return self._name
    @classmethod
    def set_global_ip_name(cls,name):
        if not isinstance(name,str):
            raise TypeError('name must be "str".')
        cls._global_ip_name = name
    def __setattr__(self,key,val):
        if key=='name':
            self._name = val
            return
        meta_check_item(self.__dict__,key,val)
        meta_set_more_attr(self,key,val)
        type.__setattr__(self,key,val)
    def __getitem__(self,components,name=None):
        class GenModule(VModule):
            pass
        set_components(GenModule,components)
        return GenModule
class VModule(ASTNode,metaclass=VModuleMeta):
    @classmethod
    def set_ip_name(cls,name):
        if not isinstance(name,str):
            raise TypeError('name must be "str".')
        cls._ip_name = name
    @property
    def name(self):
        if self._name==None:
            self._name = 'T_%d'%ASTNode.global_object_id
            ASTNode.global_object_id += 1
            warnings.warn('Missing name, auto-fixed.')
        if self._scope==None:
            return self._name
        name = self._scope.name
        if name==None:
            return self._name
        if self._name==None:
            return name
        return name+'_'+self._name
    def __getattr__(self,key):
        if hasattr(type(self)):
            val = getattr(type(self))
            if isinstance(val,(ASTNode,VStruct)):
                warnings.warn('Operating class attribute "%d".'%key)
        return object.__getattr__(self,key)
    def __setattr__(self,key,val):
        if key=='name':
            self._name = val
            return
        if isinstance(val,Expr):
            if not hasattr(type(self),key):
                raise KeyError('Module "%s" do not have any port named "%s".'%(self.name,key))
            target = getattr(type(self),key)
            if not isinstance(target,Wire):
                raise KeyError('"%s" object is not a "Wire".'%(str(type(target))))
            if target.io==None:
                raise KeyError('Wire "%s" is not a port.'%target.name)
            if not isinstance(val,Wire):
                warnings.warn('Assigning expression to port.')
            elif val.length>1:
                raise ValueError('RAM-like object "%s" cannot be assigned to port.'%val.name)
            if target.io in {'output','inout'}:
                if not isinstance(val,Wire):
                    raise KeyError('Assigning expr "%s" to output port "%s"'%(str(val),target))
                elif val.typename=='reg':
                    raise KeyError('Assigning reg "%s" to output port "%s"'%(val.name,target))
            VChecker.fix_width(val,len(target))
        object.__setattr__(self,key,val)
    def __init__(self,name=None):
        self._name = name
        self._scope = None
        self.comments = []
        self.typename = 'module'
    @classmethod
    def ports(self):
        passed = {}
        for key,val in self.mydict.items():
            if not isinstance(val,Wire):
                continue
            if val.io==None:
                continue
            val_name = val.name
            if val_name in passed:
                if val is passed[val_name]:
                    continue
                else:
                    raise RuntimeError('Redefined wire "%s" with name "%s".'%(val.name,key))
            passed[val_name] = val
            yield val
    @classmethod
    def save(cls,dir='../../gen/temp/',language='verilog',*args,printed=None,**kwargs):
        if hasattr(cls,'ip_only') and cls.ip_only == True:
            return
        if printed==None:
            printed={}
        if isinstance(language,str):
            language = code_generators[language](*args,**kwargs)
        if cls.name in printed:
            if cls == printed[cls.name]:
                return
            if language.gen(cls)!=printed[cls.name]:
                raise TypeError('Conflicting definition of module "%s"'%cls.name)
            return
        printed[cls.name] = language.gen(cls)
        if isinstance(dir,str):
            if dir[-1]!='/':
                dir += '/'
        if isinstance(dir,str):
            f = open(dir+cls.name+'.v','wt')
            print(printed[cls.name],file=f)
            f.close()
        else:
            f = dir
            print(printed[cls.name],file=f)
        for key in cls.mydict:
            val = cls.mydict[key]
            if isinstance(val,VModule):
                val.save(*args,dir=dir,language=language,printed=printed,**kwargs)