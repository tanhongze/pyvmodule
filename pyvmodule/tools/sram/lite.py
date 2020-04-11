from pyvmodule.develope import *
class SRamIF(VStruct):
    @property
    def nbyte(self):return 1<<self.level
    @property
    def width(self):return 8<<self.level
    def __init__(self,pawidth=32,nbyte=4,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.pawidth = pawidth
        self.level = clog2(nbyte)
        assert self.nbyte == nbyte

        self.en  = Wire(width=1,io=io)
        self.wen = Wire(width=self.nbyte,io=io)
        self.addr = Wire(width=self.pawidth,io=io)
        self.rdata = Wire(width=self.width,io=io)
        self.wdata = Wire(width=self.width,io=io)
    def ram(self,level,initfile=None):
        mem = VStruct()
        mem.level = level - self.level
        mem.enable_ssa('bank')
        mem.index = Wire(self.addr[self.level:level])
        for i in range(self.nbyte):
            mem.bank = Reg(width=8,length=1<<mem.level)
            mem.bank.rdata = Reg(width=8)
            self.rdata[8*i::8] = mem.bank.rdata
            blk1 = When(self.wen[i])[mem.bank[mem.index]:self.wdata[8*i::8]]
            blk2 = blk1.Otherwise[mem.bank.rdata:mem.bank[mem.index]]
            blk3 = When(self.en)[blk2]
        if not initfile is None:
            mem.initblk = Initial()        
            for i in range(self.nbyte):
                mem.initblk[vfunction.readmemh(initfile+'.%d.dat'%i,mem.banks[i])]
        return mem
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
        slave = SRamIF(pawidth=self.pawidth,nbyte=self.nbyte,io=io)
        slave.en  [:] = self.en & self.sel
        slave.wen [:] = self.wen
        slave.addr[:] = self.addr
        self.rdata.assignment = self.rdata.assignment | slave.rdata.validif(self.sel.last)
        slave.wdata[:] = self.wdata
        return slave
