__all__ = ['CodeGen','code_generators']
class CodeGen:
    from .common import precedences_list
    from .common import precedences
class GenDict(dict):
    def load_verilog(self):
        from .veriloggen import VerilogGen
        self['verilog'] = VerilogGen
    def __getitem__(self,key):
        if key in self:
            return dict.__getitem__(self,key)
        if hasattr(self,'load_'+key):
            getattr(self,'load_'+key)()
        return dict.__getitem__(self,key)
code_generators = GenDict()