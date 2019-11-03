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
from .naming import NamingNode
from .check import VChecker
class VList:
    list_format = '*_%d'
    list_start = 0
    io_translation = {'input':'output','output':'input','revert':None,None:'revert','inout':'inout'}
    @classmethod
    def set_list_format(cls,format='*_%d',start=0):
        if '*' not in format or start<0:
            raise ValueError('Invalid format string.')
        VChecker.identifier(format.replace('*','foo')%(1+cls.list_start))
        cls.list_format = format
        cls.list_start = start
        
    @classmethod
    def parse_object_error(cls,obj_str,trigger):
        if trigger:raise ValueError('Unrecognized definition format "%s".'%obj_str)
    @classmethod
    def parse_object_width(cls,obj_str,width):
        mentioned_width = None
        if len(obj_str)>0 and obj_str[-1].isdigit():
            for i in range(len(obj_str)):
                if obj_str[i].isdigit():
                    mentioned_width = int(obj_str[i:])
                    break
        if width!=None and mentioned_width!=None:cls.parse_object_error(width!=mentioned_width,obj_str)
        if width!=None:return width
        if mentioned_width!=None:return mentioned_width
        return 1
    @classmethod
    def parse_object_type(cls,obj_str,obj_type):
        count = 0
        if 'r' in obj_str:
            obj_type = 'reg'
            count+=1
        if 's' in obj_str:
            obj_type = 'struct'
            count+=1
        if 'w' in obj_str:
            obj_type = 'wire'
            count+=1
        cls.parse_object_error(obj_str,count>1)
        return obj_type
    @classmethod
    def parse_object_io(cls,obj_str,io):
        revert = io=='revert'
        io = None if io=='revert' else io
        count = 0
        if 'd' in obj_str:
            count+=1
            revert = not revert
        if 'i' in obj_str:
            count+=1
            io = 'input'
        if 'o' in obj_str:
            count+=1
            io = 'output'
        if 'x' in obj_str:
            count+=1
            io = 'inout'
        if revert:io = cls.io_translation[io]
        cls.parse_object_error(obj_str,count>1)
        return io
    @classmethod
    def parse_object(cls,obj_str,width=None,io=None,obj_type='struct'):
        if not isinstance(obj_str,str):raise TypeError('Unrecognized definition type "%s".'%str(type(obj_str)))
        parts = obj_str.split('.')
        if len(parts)==1:return parts[0],'wire',width,io
        cls.parse_object_error(obj_str,len(parts)>2)
        
        name,obj_str = parts
        for c in obj_str:cls.parse_object_error(obj_str,c.isupper())
        
        width = cls.parse_object_width(obj_str,width)
        obj_type = cls.parse_object_type(obj_str,obj_type)
        io = cls.parse_object_io(obj_str,io)
        return name,obj_type,width,io
    @classmethod
    def get_object(cls,obj_type,width,io,name=None):
        if obj_type == 'struct':return VStruct(name=name,io=io)
        if io=='revert':io = None
        if obj_type == 'reg':return Reg(width=width,io=io,name=name)
        if obj_type == 'wire':return Wire(width=width,io=io,name=name)
        raise NotImplementedError(obj_type)
    @classmethod
    def get_list_name(cls,name,i):
        if name[-1].isdigit():
            index = str(i+cls.list_start)
            return name+'_'+index
        return cls.list_format.replace('*',name)%(i+cls.list_start)
    @classmethod
    def set_components(cls,obj,components,io=None):
        if isinstance(components,dict):return cls.set_components(obj,[c for c in components.items()],io=io)
        if isinstance(components,(set,list)):
            for c in components:cls.set_components(obj,c,io=io)
            return
        if isinstance(components,str):
            name,obj_type,width,io = cls.parse_object(components,None,io,obj_type='wire')
            return setattr(obj,name,cls.get_object(obj_type,width,io,name=name))
        if not isinstance(components,tuple):
            raise TypeError(type(components))
        if len(components)!=2 and len(components)!=3:raise NotImplementedError(components)
        width = None
        if isinstance(components[1],int):width = components[1]
        obj_type='struct'
        if len(components)==2 and isinstance(components[1],(int,str)):obj_type='wire'
        
        name,obj_type,width,io = cls.parse_object(components[0],width,io=io,obj_type=obj_type)
        suffix = ''
        if isinstance(components[1],str):
            suffix,obj_type,width,io = cls.parse_object(components[1],width=width,io=io,obj_type=obj_type)
            if suffix!='':name+= '_'+suffix
        
        if len(components)==2 and isinstance(components[1],(int,str)):
            return setattr(obj,name,cls.get_object(obj_type,width,io,name=name))
        bypass = False
        if len(components)==3:
            if not isinstance(components[2],int):
                raise TypeError('count of "%s" should be int-type, not "%s">'%(components[0],type(components[2])))
            bypass = True
            if isinstance(components[1],tuple):sublist = [(cls.get_list_name(name,i),*components[1]) for i in range(components[2])]
            else:sublist = [(cls.get_list_name(name,i),components[1]) for i in range(components[2])]
        else:sublist = components[1]
        setattr(obj,name,VStruct(sublist,name=name,io=io,bypass=bypass))

class VStruct(NamingNode):
    def __init__(self,components=[],io=None,name=None,reverse=False,bypass=False):
        self.io = io
        NamingNode.__init__(self,name=name,reverse=reverse,bypass=bypass)
        VList.set_components(self,components,io=self.io)
    def __delitem__(self,key):
        del self._childs[key]
    def __setitem__(self,key,val):
        self._childs[key] = val
    def __getitem__(self,key):
        return self._childs[key]