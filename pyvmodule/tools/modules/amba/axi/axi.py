from pyvmodule.develope import *
from pyvmodule.tools.modules.sram.dual import SRamIF
from .common import init_parameter,AxiComponent,AxiGlobal
from .axi2ram import Axi2RamR,Axi2RamW
class AxiBus(AxiComponent):
    def __init__(self,g=None,**kwargs):
        init_parameter(self,**kwargs)
        if g is None:
            self.g  = AxiGlobal()
        else:
            self.aclk    = g.aclk
            self.aresetn = g.aresetn
        self.ar = self.ChannelAR(**self.channel_args)
        self.aw = self.ChannelAW(**self.channel_args)
        self.r  = self.ChannelR (**self.channel_args)
        self.w  = self.ChannelW (**self.channel_args)
        self.b  = self.ChannelB (**self.channel_args)
    def fill_disable_lock(self):
        self.arlock [:] = 0
        self.awlock [:] = 0
    def fill_disable_cache(self):
        self.arcache[:] = 0
        self.awcache[:] = 0
    def fill_disable_prot(self):
        self.arprot [:] = 0
        self.awprot [:] = 0
    def fill_disable_all(self):
        self.fill_disable_lock ()
        self.fill_disable_cache()
        self.fill_disable_prot ()
    def to_ram_r(self,*args,**kwargs):
        return Axi2RamR(self,*args,**kwargs)
    def to_ram_w(self,*args,**kwargs):
        return Axi2RamW(self,*args,**kwargs)
    def to_ram_rw(self,io=None,**kwargs):
        r = self.to_ram_r(io=io)
        w = self.to_ram_w(io=io)
        return SRamIF(r=r,w=w,io=io,**kwargs)
