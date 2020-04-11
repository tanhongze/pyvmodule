from pyvmodule.develope import *
class EventCounter(VStruct):
    _handle_prefix = 'handle_'
    def __init__(self,reset):
        self.reset = reset
        self._names = []
        for key in type(self).__dict__:
            if not key.startswith(self._handle_prefix):continue
            name = key[len(self._handle_prefix):]
            self._names.append(name)
            setattr(self,name,Reg(32))
    def capture(self,*args,**kwargs):
        for name in self._names:
            getattr(self,'handle_'+name)(getattr(self,name),*args,**kwargs)
    def increase_when(self,count,condition):
        count.valid = Wire(condition)
        count[:] = When(self.reset)[0].When(count.valid)[count+1]