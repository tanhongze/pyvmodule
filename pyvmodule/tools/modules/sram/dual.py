from pyvmodule.develope import *
class SRamRW(VStruct):
    @property
    def blevel(self):return self._blevel
    @property
    def bwidth(self):return 1<<self.blevel
    @bwidth.setter
    def bwidth(self,bwidth):
        self._blevel = clog2(bwidth)
        assert self.bwidth == bwidth
    @property
    def dwidth(self):return self.bwidth<<3
    def __init__(self,awidth=32,bwidth=4,io='auto',**kwargs):
        VStruct.__init__(self,**kwargs)
        self.awidth = awidth
        self.bwidth = bwidth
        for name,width in self.signals:
            setattr(self,name,Wire(width,io=io))
        self.enable_ssa('sel')
class SRamR(SRamRW):
    @property
    def signals(self):
        if not hasattr(self,'_signals'):
            self._signals = [
                ('addr',self.awidth),
                ('data',self.dwidth),
                ('en'  ,1),]
        return self._signals
    def subtarget(self,base,depth):
        self.sel = Wire(self.addr[depth:].equal_to(base>>depth))
        self.sel.last = Reg()
        self.sel.last[:] = self.sel
        return self.sel
    def endtarget(self):
        self.data[:] = self.data.so_far
    def remaining(self,io=None,**kwargs):
        sel = 0
        last = 0
        for i in range(len(self.sels)):
            sel |= self.sels[i]
            last|= self.sels[i].last
        self.sel = Wire(~sel)
        self.sel.last = Wire(~last)
    def resend(self,slave):
        slave.en  [:] = self.en & self.sel
        slave.addr[:] = self.addr
        self.data.so_far = (self.data.so_far if hasattr(self.data,'so_far') else 0) | slave.data.validif(self.sel.last)
class SRamW(SRamRW):
    @property
    def signals(self):
        if not hasattr(self,'_signals'):
            self._signals = [
                ('addr',self.awidth),
                ('data',self.dwidth),
                ('strb',self.bwidth),
                ('en'  ,1),]
        return self._signals
    def subtarget(self,base,depth):
        self.sel = Wire(self.addr[depth:].equal_to(base>>depth))
    def remaining(self,io=None,**kwargs):
        sel = 0
        for i in range(len(self.sels)):
            sel |= self.sels[i]
        self.sel = Wire(~sel)
    def resend(self,slave):
        slave.en  [:] = self.en & self.sel
        slave.data[:] = self.data
        slave.strb[:] = self.strb
        slave.addr[:] = self.addr
class SRam(VStruct):
    @staticmethod
    def load_init(mem,dat):
        if dat is None:return
        if dat.endswith('.mif'):
            mem.readinit = Initial()[vfunction.readmemb(dat,mem)]
        elif dat.endswith('.dat'):
            mem.readinit = Initial()[vfunction.readmemh(dat,mem)]
        else:raise NotImplementedError(dat)
    def __init__(self,r,w,level,dat=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.r = r
        self.w = w
        self.mem  = Reg(width=r.dwidth,length=1<<(level-r.blevel))
        self.load_init(self.mem,dat)

        self.mem.rdata = Reg(r.dwidth)
        When(self.r.en)[self.mem.rdata:self.mem[self.r.addr]]
        self.r.data[:] = self.mem.rdata

        self.mem.wdata = Wire(len(self.w.data))
        for i in range(len(self.w.strb)):
            self.mem.wdata[i*8::8] = self.w.strb[i].mux(self.w.data[i*8::8],self.mem[self.w.addr][i*8::8])
        When(self.w.en)[self.mem[self.w.addr]:self.mem.wdata]
class SRamIF(VStruct):
    @property
    def awidth(self):return self.r.awidth
    @property
    def bwidth(self):return self.r.bwidth
    def __init__(self,awidth=32,bwidth=4,r=None,w=None,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.r = SRamR(awidth=awidth,bwidth=bwidth,io=io) if r is None else r
        self.w = SRamW(awidth=awidth,bwidth=bwidth,io=io) if w is None else w
    def ram(self,level,dat=None,**kwargs):
        return SRam(self.r,self.w,level,dat=dat,**kwargs)
    def request_zero(self):
        self.r.en[:] = 0
        self.r.addr[:] = 0
        self.w.en[:] = 0
        self.w.addr[:] = 0
        self.w.data[:] = 0
    def response_zero(self):
        self.r.data[:] = 0
    def subtarget(self,base,depth,io=None):
        self.r.subtarget(base,depth)
        self.w.subtarget(base,depth)
        return self._subtarget(io)
    def endtarget(self):
        self.r.endtarget()
    def remaining(self,io=None,**kwargs):
        self.r.remaining()
        self.w.remaining()
        slave = self._subtarget(io)
        self.endtarget()
        return slave
    def _subtarget(self,io):
        slave = SRamIF(awidth=self.awidth,bwidth=self.bwidth,io=io)
        self.r.resend(slave.r)
        self.w.resend(slave.w)
        return slave
    @property
    def active(self):return self.r.en|self.w.en
    @property
    def write(self):return self.w.en
    @property
    def read(self):return self.r.en
    @property
    def address(self):return self.r.addr
    @property
    def write_address(self):return self.w.addr
    @property
    def read_address(self):return self.r.addr
    @property
    def write_data(self):return self.w.data
    @property
    def read_data(self):return self.r.data
MBridge = SRamIF
