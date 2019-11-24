__all__ = ['MacroManager']
def walk_items(self,prefix=None):
    if prefix==None:prefix=[]
    for key,val in self.items():
        assert isinstance(key,str)
        if isinstance(val,dict):
            for key,val in walk_items(val,['_'.join(prefix+[key.upper()])]):
                yield key,val
        else:
            if isinstance(val,(list,tuple)):raise TypeError(type(val),val)
            yield '_'.join(prefix+[key.upper()]),str(val)
class MacroManager(dict):
    def save_verilog(self,file,key,val):
        if not key[0].isalpha():raise KeyError('Invalid macro definition "%s".'%key)
        block = []
        for part1 in val.split('\\\\'):
            lines = []
            for part2 in part1.split('\\\n'):
                for part3 in part2.split('\n'):
                    lines.append(part3)
            block.append('\\\n'.join(lines))
        block = '\\\\'.join(block)
        macro = '`define %s %s%s'%(key,'\\\n' if '\n' in block else '',block)
        print(macro,file=file)
    def save(self,file=None,language='verilog'):
        print(file)
        need_close = False
        if isinstance(file,str):
            file = open(file,'wt')
            need_close = True
        else:
            import sys
            if file==None:
                file = sys.stdout
            if not isinstance(file,type(sys.stdout)):raise TypeError(file)
        printed={}
        for key,val in walk_items(self):
            if key not in printed:printed[key]=val
            elif val!=printed[key]:raise KeyError('Redefined macro "%s" with confliting "%s" or "%s"'%(key,val,printed[key]))
            getattr(self,'save_%s'%language)(file,key,val)
        if need_close:file.close()