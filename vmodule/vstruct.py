#----------------------------------------------------------------------
#pyvmodule:vstruct.py
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
from .expr import Wire
from .expr import Reg
def gen_xml(vs,hist=None):
    if hist==None:
        hist = []
    lines = []
    lines.append('<vstruct name="'+str(vs._name)+'">')
    for key,val in vs.__dict__.items():
        if key[0]=='_':
            continue
        for other in hist:
            if other is val:
                print(lines)
                raise RuntimeError(key)
        if isinstance(val,(VStruct,Wire)):
            hist.append(val)
            if isinstance(val,Wire):
                lines.append('<'+str(val.typename)+' name="'+str(val)+'" io='+str(val.io)+'/>')
            else:
                lines.append(gen_xml(val,hist=hist))
    lines.append('</ vstruct>')
    return '\n'.join(lines)
def parse_object(obj_str,width=None,io=None):
    parts = obj_str.split('.')
    if len(parts)==1:
        return parts[0],'wire',width,io
    if len(parts)>2:
        raise ValueError('Unrecognized definition format "%s".'%obj_str)
    name = parts[0]
    obj_str = parts[1]
    for c in obj_str:
        if c.isupper():
            raise ValueError('Unrecognized definition format "%s".'%obj_str)
    if width==None:
        if obj_str[-1].isdigit():
            for i in range(len(obj_str)):
                if obj_str[i].isdigit():
                    width = int(obj_str[i:])
                    break
        else:
            width = 1
    obj_type = 'wire'
    if 'r' in obj_str:
        obj_type = 'reg'
    if 's' in obj_str:
        obj_type = 'struct'
    if io=='revert':
        revert = True
    else:
        revert = False
    if 'd' in obj_str:
        revert = not revert
    if 'i' in obj_str:
        io = 'input'
    if 'o' in obj_str:
        io = 'output'
    if 'x' in obj_str:
        io = 'inout'
        
    if revert:
        translation = {'input':'output','output':'input','revert':None,None:'revert','inout':'inout'}
        io = translation[io]
    if io=='inout':
        if 'i' in obj_str:
            raise ValueError('Conflicting definition of port type with hint "%s".'%obj_str)
        if 'o' in obj_str:
            raise ValueError('Conflicting definition of port type with hint "%s".'%obj_str)
    if io=='output':
        if 'i' in obj_str:
            raise ValueError('Conflicting definition of port type with hint "%s".'%obj_str)
    if obj_type=='struct':
        if 'r' in obj_str:
            raise ValueError('Conflicting definition of port type with hint "%s".'%obj_str)
        if 'w' in obj_str:
            raise ValueError('Conflicting definition of port type with hint "%s".'%obj_str)
    if obj_type=='reg':
        if 'w' in obj_str:
            raise ValueError('Conflicting definition of port type with hint "%s".'%obj_str)
    return name,obj_type,width,io
def get_object(obj_type,width,io,name=None):
    if io=='revert':
        io = None
    if obj_type == 'reg':
        return Reg(width=width,io=io,name=name)
    return Wire(width=width,io=io,name=name)
def set_components(obj,components,io=None):
    if isinstance(components,dict):
        clist = []
        for c in components.items():
            sublist = set_components(obj,c,io=io)
            clist.extend(sublist)
        return clist
    if isinstance(components,(set,list)):
        clist = []
        for c in components:
            sublist = set_components(obj,c,io=io)
            clist.extend(sublist)
        return clist
    if isinstance(components,tuple):
        if len(components)!=2 and len(components)!=3:
            raise NotImplementedError()
        if not isinstance(components[0],str):
            raise TypeError('Unrecognized definition type "%s".'%str(type(components[0])))
        if isinstance(components[1],int):
            width = components[1]
        else:
            width = None
        name,obj_type,width,io = parse_object(components[0],width,io=io)
        if isinstance(components[1],str):
            suffix,obj_type,width,io = parse_object(components[1],width=width,io=io)
        else:
            suffix = ''
        if suffix!='':
            name+= '_'+suffix
        if len(components)==2:
            if isinstance(components[1],(int,str)):
                subobj = get_object(obj_type,width,io,name=name)
                setattr(obj,name,subobj)
                return [subobj]
            elif isinstance(components[1],(dict,list)):
                subobj = VStruct(components[1],name=name,io=io)
                setattr(obj,name,subobj)
                return [subobj]
        elif isinstance(components[2],int):
            if isinstance(components[1],tuple):
                subobj = VStruct([(name+'_%d'%i,*components[1]) for i in range(components[2])],name='',io=io,bypass=True)
                setattr(obj,name,subobj)
                return [subobj]
            else:
                subobj = VStruct([(name+'_%d'%i,components[1]) for i in range(components[2])],name='',io=io,bypass=True)
                setattr(obj,name,subobj)
                return [subobj]
        if len(components)==2:
            raise TypeError('tuple<%s,%s>'%(str(components[0]),str(type(components[1]))))
        else:
            raise TypeError('tuple<%s,%s,%s>'%(str(components[0]),str(type(components[1])),str(type(components[2]))))
            
    if isinstance(components,str):
        name,obj_type,width,io = parse_object(components,None,io)
        subobj = get_object(obj_type,width,io,name=name)
        setattr(obj,name,subobj)
        return [subobj]
    raise TypeError(type(components))

class VStruct:
    @property
    def name(self):
        _name = self._name
        if self.bypass:
            _name = None
        if self._scope==None:
            return _name
        name = self._scope.name
        if name==None:
            return _name
        if _name==None:
            return name
        return name+'_'+_name
    def __setattr__(self,key,val):
        if val is self:
            raise RuntimeError()
        object.__setattr__(self,key,val)
    def __init__(self,components=[],name=None,io=None,bypass=False):
        self._name = name
        self._scope = None
        self.bypass = bypass
        sublist = set_components(self,components,io=io)
        for c in sublist:
            if c is self:
                raise RuntimeError()
        self.__list = sublist
        for key,val in self.__dict__.items():
            if key[0] =='_':
                continue
            if isinstance(val,(Wire,VStruct)):
                val._scope = self
    def __delitem__(self,key):
        del self.__list[key]
    def __setitem__(self,key,val):
        self.__list[key] = val
    def __getitem__(self,key):
        return self.__list[key]
    def __iter__(self):
        for key,val in self.__dict__.items():
            if key[0]=='_':
                continue
            if isinstance(val,VStruct):
                for subval in val:
                    yield subval
            elif isinstance(val,Wire):
                yield val
        return
    def gen__xml(self):
        return gen_xml(self)