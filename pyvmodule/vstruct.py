#-- coding:utf-8
from .naming import NamingNode
__all__ = ['VStruct']
class VStruct(NamingNode):
    @property
    def typename(self):return 'struct'
    def __setitem__(self,key,val):
        if isinstance(key,slice):
            if not isinstance(val,NamingNode):
                raise TypeError(val,type(val))
            if key.start is None and key.stop is None and key.step is None:
                for name,target in self._naming_var.items():
                    if hasattr(val,name):target[:] = getattr(val,name)
            elif not key.start is None and not key.stop is None:
                getattr(self,key.start)[:] = getattr(val,key.stop)
            else:
                raise TypeError('[%s:%s:%s]'%(key.start,key.stop,key.step))
        elif isinstance(key,dict):
            for tname,sname in key.items():
                getattr(self,tname)[:] = getattr(val,sname)
        elif isinstance(key,(list,set)):
            for name in key:
                getattr(self,name)[:] = getattr(val,name)
        else:raise TypeError(key)
