from pyvmodule.develope import *
__all__ = ['DivUnit1','DivUnit2']
class DividorI(Wire):
    def __init__(self,a,sign,**kwargs):
        Wire.__init__(self,width=len(a),expr=a,**kwargs)
        self.sign = Wire(self[-1]&sign)
        self.abs  = Wire(self.sign.mux(~self+1,self))
        self.abs.near = Wire((self.sign**self.width)^self)
class DivUnit1(VStruct):
    '''___
   a->|DIV|->r(.,.sign)
   b->|   |->q(.,.sign)
sign->| 1 |->d
      |   |->phase
      |___|->present(.,.r,.q)
    '''
    def z(self,width):
        if width <0:return Hexadecimal(0,width=len(self.a)+width)
        else:return Hexadecimal(0,width=width)
    def p(self,value):
        return Hexadecimal(value,width=6)
    def is_same(self,c,d,r_sign,q_sign):
        same = self.r.sign.equal_to(r_sign)
        same&= self.q.sign.equal_to(q_sign)
        same&= self.a.abs.equal_to(c)
        same&= self.b.abs.equal_to(d)
        return Wire(same)
    def __init__(self,a,b,sign,io=None,opt_locs=[12,4],**kwargs):
        VStruct.__init__(self,**kwargs)
        self.a = DividorI(a,sign)
        self.b = DividorI(b,sign)
        
        self.present = Wire(self.a.equal_to(0)|self.b[1:].equal_to(0)|self.b.sign&self.b[:-1].equal_to(-1))
        self.present.r = Wire(expr=Hexadecimal(0,width=len(a)))
        self.present.q = Wire(self.b.sign.mux(self.a.neg,self.a))
        
        self.d = Wire(self.b.abs)
        self.r = Wire(len(self.a))
        self.q = Wire(len(self.a))
        self.r.sign = Wire(self.a.sign)
        self.q.sign = Wire(self.a.sign^self.b.sign)
        self.enable_ssa('loc')
        opt_locs   = sorted(opt_locs,reverse=True)
 
        self.q.val = self.z(1)*self.a.abs[:-1]
        self.r.val = self.a.abs[-1]*self.z(len(self.a)-1)
        self.phase = self.p(len(self.a)-1)
        for loc in opt_locs:
            if loc < 1 or loc>=len(self.a):
                print('Invalid optimize configuration, ignored.')
                continue
            self.loc = Wire((self.a.abs.near[loc:]<self.b.abs.near[:-loc])|self.b.abs.near[-loc:].reduce_or())
            self.q.val = self.loc.mux(self.z(-loc)*self.a.abs[:loc],self.q.val)
            self.r.val = self.loc.mux(self.a.abs[loc:]*self.z(+loc),self.r.val)
            self.phase = self.loc.mux(self.p(loc),self.phase)
        self.loc = Wire(self.a.abs.near<self.b.abs.near)
        self.q.val = self.loc.mux(self.z(len(self.a)),self.q.val)
        self.r.val = self.loc.mux(self.a.abs,self.r.val)
        self.phase = self.loc.mux(self.p(0),self.phase)
        self.q[:] = self.q.val
        self.r[:] = self.r.val
        self.phase = Wire(self.phase)
class DivUnit2(VStruct):
    '''      ___
r(.,.sign)->|DIV|->update(.phase,.r,.q)
q(.,.sign)->|   |->present(.,.r,.q)
         d->| 2 |
     phase->|___|
    '''
    sel_encodes = {
        'r':0x0,
        'q':0x1}
    def sel_res(self,sel):
        return Wire(sel.mux(self.present.q,self.present.r))
    def __init__(self,r,q,d,phase,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.r = Wire(r)
        self.q = q
        self.d = d
        self.last = Wire(phase.equal_to(0))
        self.update = VStruct()
        
        self.r.sub = Wire(self.r*Binary(0,width=1) - self.d*Binary(0,width=1))
        self.r.ged = Wire(~self.r.sub[-1])
        self.r.next= Wire(self.r.ged.mux(self.r.sub[:-1],self.r))
        
        self.update.phase = Wire((phase-1).validif(~self.last))
        self.update.r = Wire(self.last.mux(self.r.next,self.q[-1]*self.r.next[:-1]))
        self.update.q = Wire(len(self.q))
        self.update.q.still = Wire(self.r.ged*self.q[1:])
        self.update.q.shift = Wire(self.last.mux(self.update.q.still,Binary(0,width=1)*self.update.q.still[:-1]))
        self.update.q[:] = self.update.q.shift
        self.present = Wire(self.last&~self.r.ged)
        self.present.r = Wire(r.sign.mux(-r,r))
        self.present.q = Wire(q.sign.mux(-q,q))
