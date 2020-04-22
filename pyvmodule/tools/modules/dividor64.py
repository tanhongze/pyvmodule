from pyvmodule.develope import *
__all__ = ['Dividor','DivUnit1','DivUnit2']
class DividorI(Wire):
    def __init__(self,a,sign,cut,**kwargs):
        Wire.__init__(self,width=len(a),**kwargs)
        self[:32] = a[:32]
        self[32:] = cut.mux((a[31]&sign)**32,a[32:])
        self.sign = Wire()
        self.sign.w = Wire(sign&self[31])
        self.sign.d = Wire(sign&self[63])
        self.sign[:]= self.sign.w& cut|self.sign.d&~cut
        self.neg  = Wire(~self+1)
        self.abs  = Wire(len(a))
        self.abs[:32] = self.sign.mux(self.neg[:32],a[:32])
        self.abs[32:] = self.sign.d.mux(self.neg[32:],self.a[32:]).validif(~self.cut)
        self.abs.near = Wire((self.sign**64)^a)
class DivUnit1(VStruct):
    '''___
   a->|DIV|->r(.,.sign)
   b->|   |->q(.,.sign)
sign->| 1 |->d
 cut->|   |->phase
      |___|->present(.,.r,.q)
    '''
    def z(self,width):
        if width <0:return Hexadecimal(0,width=64-width)
        else:return Hexadecimal(0,width=width)
    def p(self,value):
        return Hexadecimal(value,width=6)
    def __init__(self,a,b,sign,cut,io=None,opt_locs=[32,12,4],**kwargs):
        VStruct.__init__(self,**kwargs)
        self.a = DividorI(a,sign,cut)
        self.b = DividorI(b,sign,cut)
        
        self.present = Wire(self.a.equal_to(0)|self.b[1:].equal_to(0)|self.b.sign&self.b[:-1].equal_to(-1))
        self.present.r = Wire(Hexadecimal(0,width=len(a)))
        self.present.q = Wire(self.b.sign.mux(self.a.neg,self.a))
        
        self.d = Wire(self.b.abs)
        self.r = Wire(64)
        self.q = Wire(64)
        self.r.sign = Wire(self.a.sign)
        self.q.sign = Wire(self.a.sign^self.b.sign)
        self.enable_ssa('loc')
        self.best  = Wire(*.validif(self.r))
        locs   = sorted(locs,reverse=True)
 
        self.q.val = self.z(1)*self.a.abs[:-1]
        self.r.val = self.a.abs[-1]*self.z(63)
        self.phase = self.p(63)
        for loc in opt_locs:
            if loc < 1 or loc>=self.width:
                print('Invalid optimize configuration, ignored.')
                continue
            self.loc = Wire((self.a.abs.near[loc:]<self.b.abs.near[:-loc])|self.b.abs.near[-loc:].reduce_or())
            self.q.val = self.loc.mux(self.z(-loc)*self.a.abs[:-loc])
            self.r.val = self.loc.mux(self.a.abs[-loc:]*self.z(+loc))
            self.phase = self.loc.mux(self.p(loc),self.phase)
        self.loc = Wire(self.a.abs.near<self.b.abs.near)
        self.q.val = self.loc.mux(self.z(64),self.q.val)
        self.r.val = self.loc.mux(self.a.abs,self.q.val)
        self.phase = self.loc.mux(self.p(0),self.phase)
        self.q[:] = self.q.val
        self.r[:] = self.r.val
        self.phase = Wire(self.phase)
class DivUnit2(VStruct):
    '''      ___
r(.,.sign)->|DIV|->update(.phase,.r,.q)
q(.,.sign)->|   |->present(.,.r,.q)
     phase->| 2 |
         d->|___|
    '''
    def __init__(self,r,q,phase,d,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.r = Wire(r)
        self.q = q
        self.d = d
        self.last = Wire(phase.equal_to(0))
        self.update = VStruct()
        
        self.r.sub = Wire(self.r*Binary(0,width=1) - self.d*Binary(0,width=1))
        self.r.ltd = Wire(self.r.sub[-1])
        self.r.next= self.r.ltd.mux(self.r,self.r.sub[:-1])
        
        self.update.phase = Wire((phase-1).validif(~self.last))
        self.update.r = Wire(self.last.mux(self.r.next,self.q[-1]*self.r.next[:-1]))
        self.update.q = Wire(self.last.mux(~self.r.ltd&self.q[1:],Binary(0,width=1)*self.q[:-1]))
        
        self.present = Wire(self.last&self.dividend.ltd)
        self.present.r = Wire(r.sign.mux(-r,r))
        self.present.q = Wire(q.sign.mux(-q,q))
