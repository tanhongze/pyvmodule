from pyvmodule.develope import *
from pyvmodule.tools.memorization import memorized
from .axi import AxiBus as Bus
from .common import AxiGlobal
__all__ = ['RamdomMask','NoneMask','DeterminedMask','delay']
class AxiDelayMask(VStruct):
    def changes(self,channel):return Bus.ctrl_signals[channel]
    def passing(self,channel):return Bus.data_signals[channel]
    def set_reset(self,reset):
        if hasattr(self,'reset'):self.reset[:] = reset
    def __call__(self,m,s):
        for name in Bus.channels:
            if hasattr(getattr(self,name),'ok'):
                getattr(self,name).ok[:] = getattr(s,name+'valid')&getattr(s,name+'ready')
        for name in Bus.master_channels:
            s[{name for name in self.passing(name)}] = m
            getattr(s,name+'valid')[:]=  getattr(m,name+'valid')&getattr(self,name)
            getattr(m,name+'ready')[:]=  getattr(s,name+'ready')&getattr(self,name)
        for name in Bus.slave_channels:
            m[{name for name in self.passing(name)}] = s
            getattr(m,name+'valid')[:]=  getattr(s,name+'valid')&getattr(self,name)
            getattr(s,name+'ready')[:]=  getattr(m,name+'ready')&getattr(self,name)
        return self
class RamdomMask(AxiDelayMask):
    def __init__(self,seed=0x5500ff,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.ramdom_width = 23
        self.reset = Wire()
        self.random = Reg(self.ramdom_width,io='input' if seed == 'input' else None)
        self.short_delay = Reg()
        self.no_delay    = Reg()
        self.random.next = Wire(self.ramdom_width)
        self.random.next[1:] = self.random[:-1]
        self.random.next[:1] = self.random[-1]^self.random[17]
        When(self.reset)\
            [self.random:seed]\
            [self.short_delay:self.random[: 8].equal_to(  0xff)]\
            [self.no_delay   :self.random[:16].equal_to(0x00ff)]\
        .Otherwise[self.random:self.random.next]
        for i in range(5):
            setattr(mask,self.channels[i],Wire())
            getattr(mask,self.channels[i]).raw = Wire(self.get_random(i))
        for name in channels[:3]:
            getattr(mask,name).disable = Reg()
            getattr(mask,name).ok = Wire(getattr(s,name+'valid')&getattr(s,name+'ready'))
            blk = When(self.reset)[0]
            blk = blk.When(getattr(mask,name).ok)[0]
            blk = blk.When(getattr(s,name+'valid'))[1]
            getattr(mask,name).disable[:] = blk
            getattr(mask,name)[:] = getattr(mask,name).raw|getattr(mask,name).disable
        for name in channels[3:]:
            getattr(mask,name)[:] = getattr(mask,name).raw
class NoneMask(AxiDelayMask):
    def __init__(self,**kwargs):
        VStruct.__init__(self,**kwargs)
        for name in Bus.channels:
            setattr(self,name,Binary(1,width=1))
class DeterminedMask(AxiDelayMask):
    def __init__(self,delay_r=25,delay_b=3,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.reset = Wire()
        for name in Bus.master_channels:
            setattr(self,name,Binary(1,width=1))
        for name in Bus.slave_channels:
            setattr(self,name,Wire())
        self.r.delay = delay_r
        self.b.delay = delay_b
        for name in Bus.slave_channels:
            getattr(self,name).timer = Reg(clog2(getattr(self,name).delay+1))
            getattr(self,name)[:] = getattr(self,name).timer.equal_to(0)
            getattr(self,name).ok = Wire()
            blk = When(self.reset)[0]
            blk = blk.When(getattr(self,name).ok)[getattr(self,name).delay]
            blk = blk.When(~getattr(self,name))[getattr(self,name).timer-1]
            getattr(self,name).timer[:] = blk
def delay(delay,name='axi_delay',**kwargs):
    delay_name = name
    class axi_delay(VModule):
        name = delay_name
        s = Bus(io='auto',**kwargs)
        m = Bus(g=s,io='auto',**kwargs)
        clock = aclk
        mask = delay(m,s)
        mask.set_reset(~aresetn)
    return axi_delay
