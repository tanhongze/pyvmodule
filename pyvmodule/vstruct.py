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
from .wire import Wire,Reg
from .naming import NamingNode
__all__ = ['VStruct','get_components','set_components','declare_components']
info_table = {
    0x01:(None,Wire),
    0x02:(None,Reg ),
    0x11:('output',Wire),
    0x12:('output',Reg ),
    0x21:('input',Wire)}
f_wire = 0x01
f_stru = 0x04
def get_width(decl):
    for i in range(len(decl)):
        if decl[i].isdigit():return int(decl[i:])
    return 1
def parse_object(decl,flag):
    newflag = 0x01 if 'w' in decl else 0x0
    newflag|= 0x02 if 'r' in decl else 0x0
    newflag|= 0x04 if 's' in decl else 0x0
    newflag|= 0x10 if 'o' in decl else 0x0
    newflag|= 0x20 if 'i' in decl else 0x0
    newflag|= 0x40 if 'd' in decl else 0x0
    
    # check type conflict
    if newflag&0x07==0:newflag|=flag&0x07
    elif newflag&0x03==0x03:raise ValueError('Conflicting declaration "%s", connot be both reg and wire.'%decl)
    elif newflag&0x05==0x05:raise ValueError('Conflicting declaration "%s", connot be both wire and struct.'%decl)
    elif newflag&0x06==0x06:raise ValueError('Conflicting declaration "%s", connot be both reg and struct.'%decl)
    # check i/o conflict
    if newflag&0x30==0x30:raise ValueError('Conflicting declaration "%s", connot be both input and output.'%decl)
    
    # inverts dual if dual passed
    newflag^=flag&0x40
    
    # set i/o if i/o passed
    if newflag&0x30==0x00:newflag|=flag&0x30
    
    # inverts i/o if dual
    if newflag&0x40==0x40:newflag^=0x30
    
    if newflag&0x07==0x04:
        return VStruct,{},newflag&0x77
    else:
        io,cls = info_table[newflag&0x37]
        return cls,{'width':get_width(decl),'io':io},newflag&0x47
# 'x.or32'
# 'y.iw32'
# ... ...
def parse_str(decl,flag):
    info = decl.split('.')
    if len(info)>2:raise ValueError('Multiple "." in a single decl string "%s".'%decl)
    name = None if len(info[0])==0 else info[0]
    typestr = info[1]
    cls,kwargs,flag = parse_object(typestr,flag)
    return name,cls(**kwargs),flag
# ('name','.w',3)
# ('name.w',3)
# ('name','.w3')
# ('name.w3',)
# ('name',['child1','child2'])
# ('name',['child1','child2'],3)
def parse_tuple(decl,flag):
    if not isinstance(decl,tuple):raise TypeError()
    if len(decl)<=0:raise ValueError('Invalid declare information "%s"'%str(decl))
    if len(decl)==1:return declare_components(decl[0],flag)
    
    component_types = (tuple,list,dict)
    if isinstance(decl[-1],component_types):
        name,obj,flag_new = parse_tuple(decl[:-1],flag)
        set_components(obj,decl[-1],flag=flag_new)
        return name,obj,flag
    if isinstance(decl[-2],component_types):
        if not isinstance(decl[-1],int):raise TypeError()
        return
    if not isinstance(decl[-1],(int,str)):raise TypeError()
    for i in range(len(decl)-1):
        if not isinstance(decl[-1],str):raise TypeError()
    if isinstance(decl[-1],int):
        if decl[-2][-1].isdigit():raise ValueError()
    return parse_str(''.join(str(s) for s in decl),flag&0x7,flag)
    for i in range(len(decl)):
        if isinstance(decl[i],):
            parse_tuple(decl[:i],flag)
            
            return
def get_init_flag(io):
    if io is None:return 0x00
    elif io=='input':return 0x20
    elif io=='output':return 0x10
    else:raise ValueError(io)
def set_components(obj,infos,io=None,flag=None):
    if flag is None:flag = get_init_flag(io)
    if isinstance(infos,dict):
        for key,decl in infos.items():
            if isinstance(decl,(set,list,dict)):
                val = VStruct(decl)
                setattr(obj,key,val)
            else:
                name,val,newflag = parse_target(decl,flag)
                if name is None:setattr(obj,key,val)
                else:
                    child = VStruct()
                    setattr(child,name,val)
                    setattr(obj,key,child)
    elif isinstance(infos,(set,list)):
        for decl in infos:
            set_components(obj,decl,flag=flag)
    else:
        name,val,newflag = parse_target(infos,flag)
        setattr(obj,name,val)
def parse_target(infos,flag):return parse_str(infos,flag|f_wire) if isinstance(infos,str) else parse_tuple(infos,flag)
def declare_components(infos,io=None,flag=None):
    if flag is None:flag = get_init_flag(io)
    name,val,newflag = parse_target(infos,flag)
    if not name is None:val.name = name
    return val
class VStruct(NamingNode):
    @property
    def typename(self):return 'struct'
    def __init__(self,components=[],**kwargs):
        NamingNode.__init__(self,**kwargs)
        set_components(self,components)
    def __setitem__(self,key,val):
        if not isinstance(key,slice) and key.start is None and key.stop is None and key.step is None:
            raise TypeError(key)
        if not isinstance(val,VStruct):
            raise TypeError(val,type(val))
        for key,val in val._naming_var.items():
            target = self._naming_var.get(key,None)
            if target is None:setattr(self,key,val)
            else:target[:] = getattr(val,key)
    def _node_clone(self):return VStruct(reverse=self._reverse,bypass=self._bypass)
    def __iter__(self):
        for name,var in self._naming_var.items():yield var