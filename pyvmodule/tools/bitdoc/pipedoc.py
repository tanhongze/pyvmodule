#coding=utf-8
from pyvmodule.tools.pipeline import DataLine,PipeLine
from .bitdoc import BitDoc,Entry

__all__ = ['PipeDoc','PipeEntry']

class PipeEntry(Entry):
    width = Entry.int_property('width')
class PipeDoc(BitDoc):
    def __init__(self,filename,sheetnames,Entry=PipeEntry,**kwargs):
        BitDoc.__init__(self,filename,sheetnames,Entry,**kwargs)
    @property
    def pipenames(self):
        return [name for name in self.entries[0].sheet.titles if name.endswith('P') or name.endswith('O')]
    def get_pipeline(self,pipename,my_subsets):
        my_from_prev = set()
        my_infos = []
        for entry in self.entries:
            if getattr(entry,pipename) == 'P':
                my_from_prev.add(entry.name)
                my_infos.append((entry.name,entry.width))
            elif getattr(entry,pipename) == 'Y':
                my_infos.append((entry.name,entry.width))
        PipeType = None
        if pipename.endswith('P'):PipeType = PipeLine
        elif pipename.endswith('O'):PipeType = DataLine
        else:raise NameError()
        class PipeData(PipeType):
            subsets   = my_subsets
            from_prev = my_from_prev
            _infos    = my_infos
        return PipeData
    @property
    def subsets(self):
        my_subsets = {}
        for entry in self.entries:
            if entry.subset in my_subsets:
                my_subsets[entry.subset].add(entry.name)
            else:
                my_subsets[entry.subset] = {entry.name}
        return my_subsets
    @property
    def pipelines(self):
        my_subsets = self.subsets
        stages = [self.get_pipeline(pname,my_subsets) for pname in self.pipenames]
        return tuple(stages)
