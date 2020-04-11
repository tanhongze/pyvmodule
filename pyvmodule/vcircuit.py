from .ast import ASTNode
from .vmodule import VModuleMeta,VModuleHelper
class VCircuit:
    def add_module_cascade(self,h,**kwargs):
        self.modules[h.name] = h
        for subm in h.modules:
            cls = type(subm)
            if not isinstance(cls,VModuleMeta):raise TypeError(cls)
            name = cls.name
            if cls.ip_only == True:continue
            if name in self.modules:
                if cls is self.modules[name].module:continue
                helper = VModuleHelper(cls,**kwargs)
                if helper.code == self.modules[name].code:continue
                raise TypeError('Conflicting definition of module "%s"'%name)
            else:
                helper = VModuleHelper(cls,**kwargs)
            self.add_module_cascade(helper,**kwargs)
    def save(self,**kwargs):
        getattr(self,'save_'+ASTNode.get_language())(**kwargs)
    def save_verilog(self,dir=None,**kwargs): 
        if dir is None:
            for name,helper in self.modules.items():
                print(helper.code)
            return
        if dir[-1]!='/':dir += '/'
        for name,helper in self.modules.items():
            f = open(dir+name+'.v','wt')
            print(helper.code,file=f)
            f.close()
    def __init__(self,top,**kwargs):
        self.top = top
        self.modules = {}
        if not isinstance(top,VModuleMeta):top = type(top)
        if not isinstance(top,VModuleMeta):raise TypeError(top)
        self.add_module_cascade(VModuleHelper(top,**kwargs),**kwargs)
