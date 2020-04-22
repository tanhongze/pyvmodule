from pyvmodule.develope import *

def init_parameter(self,awidth=64,bwidth=None,size_v=None,dwidth=None,ignores=set(),io='auto',iwidth=4,lwidth=4,**kwargs):
    VStruct.__init__(self,**kwargs)
    self.ignores= ignores
    self.io = io
    self.awidth = awidth
    self.iwidth = iwidth
    self.lwidth = lwidth
    self.dwidth = dwidth
    self.bwidth = bwidth
    self.size_v = size_v
    if not self.dwidth is None:
        self.bwidth = self.dwidth>>3
        if not bwidth is None and self.bwidth != bwidth:raise ValueError('%d-bits or %d-bits?'%(self.dwidth,bwidth<<3))
    if not self.bwidth is None:
        self.size_v = clog2(self.bwidth)
        if not size_v is None and self.size_v != size_v:raise ValueError('%d-bytes or %d-bytes?'%(self.bwidth,1<<size_v))
    if self.size_v is None:self.size_v = 2
    self.bwidth = 1<<self.size_v
    self.dwidth = self.bwidth<<3
    if self.size_v > 7:
        raise ValueError('Width of AXI-data should not be more than 1024-bits.')
    if not bwidth is None and self.bwidth!=bwidth:
        raise ValueError('%d-bytes AXI-data is not allowed, could use %d instead?.'%(bwidth,self.bwidth))
    if not dwidth is None and self.dwidth!=dwidth:
        raise ValueError('%d-bits AXI-data is not allowed, could use %d instead?.'%(dwidth,self.dwidth))
    return kwargs
def update_data_burst_addr(addr,burst):
    
    addr.fixed = Wire(addr)
    addr.incr  = Wire(len(addr))
    addr.wrap  = Wire(len(addr))

    addr.next  = 0
    for name in ['fixed','incr','wrap']:
        mode = Wire(burst.equal_to(AxiComponent.burst_types[name]))
        setattr(burst,name,mode)
        addr.next|= getattr(addr,name).validif(mode)
    addr.next   = Wire(addr.next)
    
    addr.update = Wire()
    return When(addr.update)[addr:addr.next]
def compute_address(addr,alen,size_v):
    if size_v >0:addr.incr[:size_v] = addr[:size_v]
    addr.incr[size_v:] = addr[size_v:]+1
    if size_v >0:addr.wrap[:size_v] = addr[:size_v]
    addr.wrap[size_v+4:] = addr[size_v+4:]
    wrap_core = addr[size_v::4]&~alen
    wrap_core|= alen&(addr[size_v::4]+1)
    addr.wrap[size_v::4] = wrap_core
my_channels = {'ar','aw','w','r','b'}
my_master_channels = {'ar','aw','w'}
my_slave_channels  = {'r','b'}
my_data_signals = {
    'ar':['arid','araddr','arlen','arsize','arburst','arlock','arcache','arprot'],
    'aw':['awid','awaddr','awlen','awsize','awburst','awlock','awcache','awprot'],
    'r' :[ 'rid', 'rdata','rresp','rlast'],
    'w' :[ 'wid', 'wdata','wstrb','wlast'],
    'b' :[ 'bid',         'bresp']}
my_ctrl_signals = {channel:[channel+'valid',channel+'ready'] for channel in my_channels}
my_signals = {channel:my_data_signals[channel]+my_ctrl_signals[channel] for channel in my_channels}

class AxiGlobal(VStruct):
    def __init__(self,io='input',mounting=False,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.aclk    = Wire(1,io=io,mounting=mounting)
        self.aresetn = Wire(1,io=io,mounting=mounting)
class AxiComponent(VStruct):
    channels = my_channels
    master_channels = my_master_channels
    slave_channels = my_slave_channels
    data_signals = my_data_signals
    ctrl_signals = my_ctrl_signals
    signals = my_signals
    burst_types = {
        'fixed':0,
        'incr' :1,
        'wrap' :2}
    resp_types = {
        'okay'   :0,
        'exokay' :1,
        'slverr' :2,
        'decerr' :3}
    @property
    def channel_args(self):
        kwargs = {
            'io':self.io,
            'bypass':True,
            'ignores':self.ignores,
            'size_v':self.size_v,
            'awidth':self.awidth,
            'iwidth':self.iwidth,
            'lwidth':self.lwidth}
        return kwargs
    class ChannelAR(VStruct):
        @property
        def signals(self):
            if hasattr(self,'_signals'):return self._signals
            self._signals = {
                'arid'   :self.iwidth,
                'araddr' :self.awidth,
                'arlen'  :self.lwidth,
                'arsize' :3,
                'arburst':2,
                'arlock' :2,
                'arcache':4,
                'arprot' :3,
                'arvalid':1,
                'arready':1}
            return self._signals
        def __init__(self,**kwargs):
            init_parameter(self,**kwargs)
            for name,width in self.signals.items():
                if name in self.ignores:continue
                setattr(self,name,Wire(width,io=self.io))
    class ChannelR(VStruct):
        @property
        def signals(self):
            if hasattr(self,'_signals'):return self._signals
            self._signals = {
                'rid'   :self.iwidth,
                'rdata' :self.dwidth,
                'rresp' :2,
                'rlast' :1,
                'rvalid':1,
                'rready':1}
            return self._signals
        def __init__(self,**kwargs):
            init_parameter(self,**kwargs)
            for name,width in self.signals.items():
                if name in self.ignores:continue
                setattr(self,name,Wire(width,io=self.io))
    class ChannelW(VStruct):
        @property
        def signals(self):
            if hasattr(self,'_signals'):return self._signals
            self._signals = {
                'wid'   :self.iwidth,
                'wdata' :self.dwidth,
                'wstrb' :self.bwidth,
                'wlast' :1,
                'wvalid':1,
                'wready':1}
            return self._signals
        def __init__(self,**kwargs):
            init_parameter(self,**kwargs)
            for name,width in self.signals.items():
                if name in self.ignores:continue
                setattr(self,name,Wire(width,io=self.io))
    class ChannelAW(VStruct):
        @property
        def signals(self):
            if hasattr(self,'_signals'):return self._signals
            self._signals = {
                'awid'   :self.iwidth,
                'awaddr' :self.awidth,
                'awlen'  :self.lwidth,
                'awsize' :3,
                'awburst':2,
                'awlock' :2,
                'awcache':4,
                'awprot' :3,
                'awvalid':1,
                'awready':1}
            return self._signals
        def __init__(self,**kwargs):
            init_parameter(self,**kwargs)
            for name,width in self.signals.items():
                if name in self.ignores:continue
                setattr(self,name,Wire(width,io=self.io))
    class ChannelB(VStruct):
        @property
        def signals(self):
            if hasattr(self,'_signals'):return self._signals
            self._signals = {
                'bid'   :self.iwidth,
                'bresp' :2,
                'bvalid':1,
                'bready':1}
            return self._signals
        def __init__(self,**kwargs):
            init_parameter(self,**kwargs)
            for name,width in self.signals.items():
                if name in self.ignores:continue
                setattr(self,name,Wire(width,io=self.io))
