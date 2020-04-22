from pyvmodule.develope import *
from pyvmodule.tools.modules.sram.dual import SRam
from .axi import AxiBus
def axi_ram(level,name='axi_ram',dat=None,**kwargs):
    ram_name = name
    class axi_ram(VModule):
        name = ram_name
        axi = AxiBus(io='auto',ignores={'arlock','arcache','arprot','awlock','awcache','awprot','wid'},**kwargs)
        clock = axi.aclk
        ram = SRam(axi.to_ram_r(),axi.to_ram_w(),level,dat=dat)
    return axi_ram
