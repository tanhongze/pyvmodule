from pyvmodule.develope import *
class ChannelAR(VStruct):
    def __init__(self,bypass=True,**kwargs):
        VStruct.__init__(self,bypass=bypass,**kwargs)
class ChannelR(VStruct):
    def __init__(self,bypass=True,**kwargs):
        VStruct.__init__(self,bypass=bypass,**kwargs)
class ChannelW(VStruct):
    def __init__(self,,bypass=True**kwargs):
        VStruct.__init__(self,bypass=bypass,**kwargs)
class ChannelWR(VStruct):
    def __init__(self,bypass=True,**kwargs):
        VStruct.__init__(self,bypass=bypass,**kwargs)
class ChannelB(VStruct):
    def __init__(self,bypass=True,**kwargs):
        VStruct.__init__(self,bypass=bypass,**kwargs)
class Channel(VStruct):
    def __init__(self,io='auto',bypass=True,**kwargs):
        VStruct.__init__(self,bypass=bypass,**kwargs)
        self.aclk    = Wire(io=io)
        self.aresetn = Wire(io=io)
        self.ar = ChannelAR(io=io)
        self.r  = ChannelR (io=io)
        self.w  = ChannelW (io=io)
        self.wr = ChannelWR(io=io)
        self.b  = ChannelB (io=io)
class AXI:
    @property
    def l_arid   (self):return self.id
    @property
    def l_araddr (self):return self.addr
    @property
    def l_arlen  (self):return 4
    @property
    def l_arsize (self):return 3
    @property
    def l_arburst(self):return 2
    @property
    def l_arlock (self):return 2
    @property
    def l_arcache(self):return 4
    @property
    def l_arprot (self):return 3
    @property
    def l_arvalid(self):return 1
    @property
    def l_arready(self):return 1
    @property
    def l_rid    (self):return self.id
    @property
    def l_rdata  (self):return self.data
    @property
    def l_rresp  (self):return 2
    @property
    def l_rlast  (self):return 1
    @property
    def l_rvalid (self):return 1
    @property
    def l_rready (self):return 1
    @property
    def l_awid   (self):return self.id
    @property
    def l_awaddr (self):return self.addr
    @property
    def l_awaddr (self):return self.l_arlen
    @property
    def l_awsize (self):return self.l_arsize
    @property
    def l_awburst(self):return self.l_arburst
    @property
    def l_awlock (self):return self.l_arlock
    @property
    def l_awcache(self):return self.l_arcache
    @property
    def l_awprot (self):return self.l_arprot
    @property
    def l_awvalid(self):return 1
    @property
    def l_awready(self):return 1
    @property
    def l_wid    (self):return self.id
    @property
    def l_wdata  (self):return self.data
    @property
    def l_wlast  (self):return 1
    @property
    def l_wvalid (self):return 1
    @property
    def l_wready (self):return 1
    @property
    def l_bid    (self):return self.id
    @property
    def l_bresp  (self):return self.rresp
    @property
    def l_bvalid (self):return 1
    @property
    def l_bready (self):return 1
    
    directions = {
        'ar':'.o',
        'r' :'.i',
        'aw':'.o',
        'w' :'.o',
        'b' :'.i',
        'arready':'.i',
        'rready' :'.o',
        'awvalid':'.i',
        'wready' :'.i',
        'bready' :'.o'}
    burst_types = {
        'fixed':0,
        'incr' :1,
        'wrap' :2}
        
    def disable_lock(self):
        self.arlock = 0
        self.awlock = 0
    def disable_cache(self):
        self.arcache = 0
        self.awcache = 0
    def disable_prot(self):
        self.arprot = 0
        self.awprot = 0
    def disable_properties(self):
        self.disable_lock()
        self.disable_cache()
        self.disable_prot()
    def set_access_type(self,name,port=None):
        if port in {None,'ar','r'}:
            self.arburst = self.burst_types[name]
        if port in {None,'aw','w'}:
            self.awburst = self.burst_types[name]
    
    def __init__(self,addr=32,data=32,id=4,buf=True):
        self.addr = addr
        self.data = data
        self.id   = id
        self.buf  = buf
        
        self.names = {}
        self.buses = {'ar','r','aw','w','b'}
        
        for port in self.buses:
            names = []
            for key in type(self).__dict__:
                if len(key)<=2+len(port):continue
                if key[:2+len(port)] != 'l_'+port:continue
                names.append(key[2:])
            self.names[port] = names
            
            # define bus for 'ar','r','aw','w','b'
            def bus(direction=None):
                ports = []
                for name in names:
                    io = None
                    buf = False if hasattr(self,name) else self.buf
                    if direction in {'master','slave'}:
                        io = self.directions[name] if name in self.directions else io
                        io = self.directions[port] if io==None else io
                        if direction == 'slave':
                            io = {'.o':'.i','.i':'.o'}[io]
                        if buf and io=='.o':
                            io+= 'r'
                    else:
                        io = '.r' if buf else '.w'
                    width = getattr(self,'l_'+name)
                    ports.append((name,io+str(width)))
                return ports
            # bus defined
            setattr(self,port,bus)
        def bus(direction=None):
            ports = []
            for port in self.buses:
                ports.append((port,getattr(self,port)(direction)))
        self.ports = bus
