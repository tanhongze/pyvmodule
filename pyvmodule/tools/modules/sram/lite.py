from pyvmodule.develope import *
class SRam(Reg):
    @staticmethod
    def load_init(mem,dat):
        if dat is None:return
        if dat.endswith('.mif'):
            mem.readinit = Initial()[vfunction.readmemb(dat,mem)]
        elif dat.endswith('.dat'):
            mem.readinit = Initial()[vfunction.readmemh(dat,mem)]
        else:raise NotImplementedError(dat)
    def __init__(self,level,rw,dat=None,**kwargs):
        alevel = level - rw.blevel
        Reg.__init__(self,width=rw.dwidth,length=1<<alevel,**kwargs)
        self.alevel = alevel
        self.blevel = rw.blevel
        self.load_init(self,dat)
        self.rw = rw
        self.addr  = Wire(rw.addr[self.blevel::self.alevel])
        self.rdata = Reg(width=rw.dwidth)
        self.enable_ssa('rodata')
        self.enable_ssa('roaddr')
        self.wdata = Wire(width=rw.dwidth)
        for i in range(rw.bwidth):
            self.wdata[i*8::8] = rw.wen[i].mux(rw.wdata[i*8::8],self[self.addr][i*8::8])
        self.we = Wire(rw.wen.reduce_or())
        When(rw.en)[self.rdata:self[self.addr]][When(self.we)[self[self.addr]:self.wdata]]
        rw.rdata[:] = self.rdata
    def read_with(self,rw):
        self.rodata = Reg(width=len(self))
        self.roaddr = Wire(rw.addr[self.blevel::self.alevel])
        if self.blevel==rw.blevel:
            When(rw.en)[self.rodata:self[self.roaddr]]
            rw.rdata[:] = self.rodata
        elif self.blevel > rw.blevel:
            self.rodata.sel = Reg()
            When(rw.en)[self.rodata:self[self.roaddr]][self.rodata.sel:rw.addr[rw.blevel:self.blevel]]
            self.rodata.sel.dec = decode(self.rodata.sel)
            data = 0
            width = len(rw.rdata)
            for i in range(len(self.rodata.sel.dec)):
                data|=self.rodata[width*i::width].validif(self.rodata.sel.dec[i])
            rw.rdata[:] = data
        else:raise ValueError('Read %d-bytes-ram with %d-bytes-bus.'%(1<<self.blevel,1<<rw.blevel))
class SRamIF(VStruct):
    @property
    def bwidth(self):return 1<<self.blevel
    @property
    def dwidth(self):return 8<<self.blevel
    def __init__(self,awidth=32,bwidth=4,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.awidth = awidth
        self.blevel = clog2(bwidth)
        assert self.bwidth == bwidth

        self.en  = Wire(width=1,io=io)
        self.wen = Wire(width=self.bwidth,io=io)
        self.addr = Wire(width=self.awidth,io=io)
        self.rdata = Wire(width=self.dwidth,io=io)
        self.wdata = Wire(width=self.dwidth,io=io)
    def ram(self,level,dat=None):
        return SRam(level,self,dat=dat)
    def request_zero(self):
        self.en[:] = 0
        self.wen[:] = 0
        self.addr[:] = 0
        self.wdata[:] = 0
    def response_zero(self):
        self.rdata[:] = 0
    @property
    def active(self):return self.en
    @property
    def write(self):return self.en & self.wen.reduce_or()
    @property
    def read(self):return self.en &~self.wen.reduce_or()
    @property
    def address(self):return self.addr
    @property
    def write_address(self):return self.addr
    @property
    def read_address(self):return self.addr
    @property
    def write_data(self):return self.wdata
    @property
    def read_data(self):return self.rdata
class MBridge(SRamIF):
    def __init__(self,*args,**kwargs):
        SRamIF.__init__(self,*args,**kwargs)
        self.enable_ssa('sel')
        self.rdata[:] = 0
    def subtarget(self,base,depth,io=None):
        self.sel = Wire(self.addr[depth:].equal_to(base>>depth))
        self.sel.last = Reg()
        self.sel.last[:] = self.sel
        return self._subtarget(io)
    def endtarget(self):pass
    def remaining(self,io=None,**kwargs):
        sel = 0
        last = 0
        for i in range(len(self.sels)):
            sel |= self.sels[i]
            last|= self.sels[i].last
        self.sel = Wire(~sel)
        self.sel.last = Wire(~last)
        return self._subtarget(io)
    def _subtarget(self,io):
        slave = SRamIF(awidth=self.awidth,bwidth=self.bwidth,io=io)
        slave.en  [:] = self.en & self.sel
        slave.wen [:] = self.wen
        slave.addr[:] = self.addr
        self.rdata.assignment = self.rdata.assignment | slave.rdata.validif(self.sel.last)
        slave.wdata[:] = self.wdata
        return slave
