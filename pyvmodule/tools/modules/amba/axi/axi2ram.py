from pyvmodule.develope import *
from pyvmodule.tools.modules.sram.dual import SRamR,SRamW
from pyvmodule.tools.modules.fifo import Fifo
from .common import AxiComponent,update_data_burst_addr,compute_address
class Axi2RamR(SRamR):
    class FifoAR(Fifo):
        def update_data_araddr(self,field):
            return update_data_burst_addr(field,self.data.arburst)
    def __init__(self,axi,io=None,**kwargs):
        SRamR.__init__(self,awidth=axi.awidth,bwidth=axi.bwidth,io=io,**kwargs)
        self.reset = ~axi.aresetn
        self.rcur  = Reg(4)
        axi.rresp[:]=0
        for name in ['rid','rlast','rvalid']:
            driver = Reg(len(getattr(axi,name)))
            getattr(axi,name)[:] = driver
            setattr(self,name,driver)
        self.a = self.FifoAR(self.reset,axi,push=axi.arvalid,
            names=['arid','araddr','arlen','arsize','arburst'],depth=0)
        compute_address(self.a.data.araddr,self.a.data.arlen,axi.size_v)
        axi.arready[:]= ~self.a.full
        self.allow_out = Wire(axi.rready|~axi.rvalid)

        self.a.data.arlen.last = Wire(self.a.data.arlen.equal_to(self.rcur))
        self.a.pop[:] = self.en&self.a.data.arlen.last
        self.a.data.araddr.update[:] = self.en&~self.a.data.arlen.last

        self.rcur.reset = Wire(self.reset|self.a.pop)
        When(self.rcur.reset)[self.rcur:0]\
        .When(self.en)[self.rcur:self.rcur+1]

        When(self.reset)[self.rvalid:0]\
        .When(self.en)[self.rvalid:1]\
        .When(axi.rready)[self.rvalid:0]

        When(self.a.pop)[self.rid:self.a.data.arid]

        When(self.en)[self.rlast:self.a.data.arlen.last]

        self.en  [:] = self.a.valid&self.allow_out
        self.addr[:] = self.a.data.araddr
        axi.rdata[:] = self.data
class Axi2RamW(SRamW):
    class FifoAW(Fifo):
        def update_data_awaddr(self,field):
            return update_data_burst_addr(field,self.data.awburst)
    def __init__(self,axi,io=None,**kwargs):
        SRamW.__init__(self,awidth=axi.awidth,bwidth=axi.bwidth,io=io,**kwargs)
        self.reset = ~axi.aresetn

        self.w = VStruct()
        for name in ['wdata','wstrb','wlast','wvalid']:
            setattr(self,name,Reg(len(getattr(axi,name))))
            
        self.a = self.FifoAW(self.reset,axi,push=axi.awvalid,
            names=['awid','awaddr','awlen','awsize','awburst'],depth=0)
        self.b  = Fifo(self.reset,self.a.data.awid,pop=axi.bready)
        axi.bid   [:]= self.b.data
        axi.bvalid[:]= self.b.valid
        axi.bresp [:]= 0
        
        compute_address(self.a.data.awaddr,self.a.data.awlen,axi.size_v)

        self.allow_out = Wire(self.a.valid&~self.b.full)
        self.a.data.awaddr.update[:] = self.en&~self.wlast
        self.a.pop [:] = self.en& self.wlast
        self.b.push [:] = self.a.pop
        
        self.go = Wire(axi.wvalid&axi.wready)
        blk = When(self.go)
        for name in ['wdata','wstrb','wlast']:
            blk[getattr(self,name):getattr(axi,name)]
        When(self.reset)[self.wvalid:0]\
        .When(self.go)[self.wvalid:1]\
        .When(self.en)[self.wvalid:0]

        axi.awready[:] = ~self.a.full
        axi.wready [:] = self.allow_out|~self.wvalid

        self.en  [:] = self.wvalid&self.allow_out&~self.reset
        self.addr[:] = self.a.data.awaddr
        self.data[:] = self.wdata
        self.strb[:] = self.wstrb
