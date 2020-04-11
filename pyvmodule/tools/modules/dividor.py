from pyvmodule.develope import *
__all__ = ['Dividor']
class DividorI(Wire):
    def __init__(self,sign,a,**kwargs):
        Wire.__init__(self,width=len(a),expr=a,**kwargs)
        self.sign = Wire(self[-1]&sign)
        self.abs  = Wire(self.sign.mux(~self+1,self))
        self.abs.near = Wire((self.sign**self.width)^self)
        
class Dividor(VStruct):
    def __init__(self,reset,req,ack,a,b,sign,io=None,locs=[12,4],**kwargs):
        VStruct.__init__(self,**kwargs)
        self.width = len(a)
        if len(b)!=self.width:raise NotImplementedError()
        self.a = DividorI(sign,a)
        self.b = DividorI(sign,b)

        self.work = Reg()
        self.done = Reg()
        self.ready = Wire(io=io)
        self.enter = Wire()
        self.finish = Wire(io=io)
        self.sloving = Wire()
        self.leave = Wire()
        self.leave[:] = self.finish & ack
        self.ready[:] = self.leave  | ~self.work
        self.enter[:] = self.ready  & req
        self.sloving[:] = self.work &~self.done&~self.finish

        self.enter.q  = Wire(self.a.equal_to(0)|self.b[1:].equal_to(0)|self.b.sign&self.b[:-1].equal_to(-1))
        self.enter.r  = Wire(self.a.abs.near<self.b.abs.near) 
        self.enter.x  = Wire(self.enter.q|self.enter.r)
        self.enter.enable_ssa('loc')
        self.enter.enable_ssa('sft')
        near_a = self.a.abs.near
        near_b = self.b.abs.near
        self.enter.best  = Wire(self.a.abs.validif(self.enter.q)*self.a.abs.validif(self.enter.r&~self.enter.q))
        self.enter.worst = Wire(Hexadecimal(0,width=1)*self.a.abs*Hexadecimal(0,width=self.width-1))
        
        Hex    = Hexadecimal
        pwidth = clog2(len(self.a))
        locs   = sorted(locs,reverse=True)
 
        phase = Hex(self.width-1,width=pwidth)
        sft   = self.enter.worst
        for loc in locs:
            if loc < 1 or loc>=self.width:
                print('Invalid optimize configuration, ignored.')
                continue
            self.enter.loc = Wire((near_a[loc:]<near_b[:-loc])|near_b[-loc:].reduce_or())
            self.enter.sft = Wire(Hex(0,width=self.width-loc)*self.a.abs*Hex(0,width=loc))
            phase = self.enter.loc.mux(Hex(loc,width=pwidth),phase)
            sft   = self.enter.loc.mux(self.enter.sft,sft)
        self.enter.val   = Wire(sft.validif(~self.enter.x)|self.enter.best)
        self.enter.phase = Wire(phase.validif(~self.enter.x))
        
        self.phase = Reg(pwidth)
        self.phase.last = Wire(self.phase.equal_to(0))
        self.phase.next = Wire((self.phase-1).validif(~self.phase.last))
        self.divisor  = Reg(self.width)
        self.buffer   = Reg(self.width*2)
        self.buffer.addq = Wire(self.width*2)
        self.buffer.next = Wire(self.width*2)
        self.dividend = Wire(self.buffer[self.width:])
        self.partial  = Wire(self.buffer[:self.width])
        
        self.divisor .ext = Wire(self.divisor *Binary(0,width=1))
        self.dividend.ext = Wire(self.dividend*Binary(0,width=1))
        self.dividend.sub = Wire(self.dividend.ext - self.divisor .ext)
        self.dividend.ltd = Wire(self.dividend.sub[-1])
        self.r = Wire(self.width,io=io)
        self.q = Wire(self.width,io=io)
        self.r.sign = Reg()
        self.q.sign = Reg()
        
        self.buffer.addq[0] = ~self.dividend.ltd
        self.buffer.addq[1:self.width]= self.partial[1:]
        self.buffer.addq[self.width: ]= self.dividend.ltd.mux(self.dividend,self.dividend.sub[:-1])
        self.buffer.next[:] = self.phase.last.mux(self.buffer.addq,Binary(0,width=1)*self.buffer.addq[:-1])
        
        self.finish[:] = self.work&self.done|self.work&self.phase.equal_to(0)&self.dividend.ltd
        self.r.sign.next = Wire(self.a.sign)
        self.q.sign.next = Wire(self.a.sign^self.b.sign)

        self.r[:] = self.r.sign.mux(~self.dividend+1,self.dividend)
        self.q[:] = self.q.sign.mux(~self.partial +1,self.partial )

        When(reset)[self.work:0]\
        .When(self.ready)[self.work:req]

        When(self.ready)[self.done:req&self.enter.q]

        When(self.enter)[self.phase:self.enter.phase]\
            [self.buffer:self.enter.val][self.divisor:self.b.abs]\
            [self.r.sign:self.r.sign.next][self.q.sign:self.q.sign.next]\
        .When(self.sloving)[self.phase:self.phase.next][self.buffer:self.buffer.next]

