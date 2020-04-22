from pyvmodule.develope import *
from pyvmodule.tools.modules.fifo import Fifo
from .axi import AxiBus as Bus
class MBridge(VStruct):
    def __init__(self,reset,m,*targets,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.m = m
        for channel in Bus.master_channels:
            fifo = Fifo(reset,m,names=Bus.data_signals[channel],push=getattr(m,channel+'valid'))
            setattr(self,channel,fifo)
            getattr(m,channel+'ready')[:] = ~fifo.full
        self.enable_ssa('s')
        self.enable_ssa('hit')
        for base,level,target in targets:
            self.hit = Wire(self.)
            self.s = target
            for channel in Bus.master_channels:
    def subtargets(self,base,range):
        self.s = AxiBus(**self.m.channel_args)
