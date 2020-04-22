from pyvmodule.develope import *
from pyvmodule.tools.memorization import memorized
def carry(p,g,i,ci=0):
    c = ci&p[:i].reduce_and()
    for j in range(1,i):
        c|=g[j-1]&p[j:i].reduce_and()
    c|= g[i-1]
    return c
def get_c(p,g,ci=0):
    c = Wire(len(p)-1)
    for i in range(1,len(p)):
        c[i-1] = carry(p,g,i,ci=ci)
    return c
def get_p(p,g):
    return p.reduce_and()
def get_g(p,g):
    return carry(p,g,len(p))
def div_upper(x,n):
    return (x//n)+(1 if x%n>0 else 0)
class Carry(Wire):
    def __init__(self,p,g,ci=0,co=None,**kwargs):
        Wire.__init__(self,len(p),**kwargs)
        if len(p)==1:
            self[:] = ci
            if not co is None:
                self.co = co
                self.co[:] = ci&p|g
            return

        self.p = p
        self.g = g
        self.co = co

        self.enable_ssa('lv')
        self.lv = self
        while len(self.lv.p)>4:
            self.lv.m = len(self.lv.p)
            self.lv.n = div_upper(self.lv.m,4)
            m,n = self.lv.m,self.lv.n

            self.lv.widths = [4 for i in range(n)]
            for i in range(4*n-m):
                self.lv.widths[i%n]-=1
            self.lv.locs = [0]*n
            for i in range(1,n):
                self.lv.locs[i] =self. lv.locs[i-1]+self.lv.widths[i-1]
            locs,widths = self.lv.locs,self.lv.widths

            lv = VStruct()
            lv.p = Wire(n)
            lv.g = Wire(n)
            for i in range(n):
                lv.p[i] = get_p(self.lv.p[locs[i]::widths[i]],self.lv.g[locs[i]::widths[i]])
                lv.g[i] = get_g(self.lv.p[locs[i]::widths[i]],self.lv.g[locs[i]::widths[i]])
            self.lv = lv
        self.lv.c  = get_c(self.lv.p,self.lv.g,ci)
        self.lv.cx = [ci]+[self.lv.c[i] for i in range(len(self.lv.c))]
        if not co is None:
            self.co = co
            self.co[:] = carry(self.lv.p,self.lv.g,len(self.lv.p),ci=ci)

        for i in range(len(self.lvs)-2,-1,-1):
            self.lvs[i].enable_ssa('c')
            n,m = self.lvs[i].n,self.lvs[i].m
            locs,widths = self.lvs[i].locs,self.lvs[i].widths
            self.lvs[i].cx = []
            for j in range(n):
                self.lvs[i].c = get_c(self.lvs[i].p[locs[j]::widths[j]],self.lvs[i].g[locs[j]::widths[j]],self.lvs[i+1].cx[j])
                self.lvs[i].cx+= [self.lvs[i+1].cx[j]]
                self.lvs[i].cx+= [self.lvs[i].cs[j][k] for k in range(len(self.lvs[i].cs[j]))]
        for i in range(len(self.cx)):
            self[i] = self.lvs[0].cx[i]
@memorized
def get_cla(width,use_ci=False,use_co=False):
    class cla(VModule):
        p = Wire(width,io='input')
        g = Wire(width,io='input')
        ci = Wire(1,io='input' ) if use_ci else 0
        co = Wire(1,io='output') if use_co else None
        c = Carry(p,g,ci=ci,co=co,io='output')
    return cla
