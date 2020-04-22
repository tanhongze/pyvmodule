from pyvmodule.develope import *
from pyvmodule.tools.pipeline import DataLine
from pyvmodule.tools.memorization import memorized
__all__ = ['BoothEncode','WallaceTree','MultiplierRoot','get_mul_root']
def s_vector(a,b,c):
    return a&~b&~c|~a&b&~c|~a&~b&c|a&b&c
def c_vector(a,b,c):
    return Binary(0,width=1)*(a[:-1]&b[:-1]|a[:-1]&c[:-1]|b[:-1]&c[:-1])
class BoothEncode(DataLine):
    @property
    def odd(self):return self.widtha&1
    @property
    def num(self):return self.widtha>>1
    @property
    def count(self):return self.num + self.odd
    @staticmethod
    def get_encode_width(widtha):
        return widtha*2 + 2
    def _init(self,widtha=32,**kwargs):
        self.widtha = widtha
        self._infos = [
            ('m1' ,self.count),
            ('m2' ,self.count),
            ('neg',self.count),
            ('ext',self.num  ),
            ('lastb',1)] + ([('lasta',1)] if not self.odd else [])
    def generated_with(self,a,b,sign):
        self.lastb[:] = sign & b[-1]
        self.neg[0] = a[1]
        self.m1 [0] = a[0]
        self.m2 [0] = a[1]&~a[0]
        self.ext[0] = self.lastb&a[0]&~a[1]|~self.lastb&a[1]
        # 1:+
        for i in range(1,self.num):
            self.neg[i] = a[2*i+1]&~(a[2*i-1]&a[2*i])
            self.m1 [i] = a[2*i-1]^a[2*i]
            self.m2 [i] = a[2*i-1]&a[2*i]&~a[2*i+1]|~a[2*i-1]&~a[2*i]&a[2*i+1]
            self.ext[i] = (a[2*i-1]|a[2*i])&~a[2*i+1]& self.lastb\
                        |~(a[2*i-1]&a[2*i])& a[2*i+1]&~self.lastb
        if self.odd:
            self.neg[self.num] = a[-1] &~a[-2] &sign
            self.m1 [self.num] = a[-1] ^ a[-2]
            self.m2 [self.num] = a[-1] & a[-2] &~sign
        else:
            self.lasta[:] = a[-1]&~sign
class WallaceTree(VStruct):
    def __init__(self,z,*zs,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.enable_ssa('s')
        self.enable_ssa('c')
        cur = (list(z) if isinstance(z,(list,tuple)) else [z]) + list(zs)
        while len(cur)>2:
            count = len(cur)//3
            for index in range(count) :
                self.s = Wire(s_vector(*cur[index*3:index*3+3]))
                self.c = Wire(c_vector(*cur[index*3:index*3+3]))
            cur = cur[count*3:] + self.ss[-count:] + self.cs[-count:]
class MultiplierRoot(VStruct):
    @property
    def odd(self):return self.widtha&1
    @property
    def num(self):return self.widtha>>1
    @property
    def count(self):return self.num + self.odd
    @property
    def widtha(self):return len(self.a)
    @property
    def widthb(self):return len(self.b)
    @property
    def widthp(self):return self.widtha+self.widthb
    def __init__(self,a,b,sign,enc=None,io=None,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.a = a
        self.b = b
        self.sign = sign
        self.enc = BoothEncode(widtha=len(a)) if enc is None else enc
        self.enc.generated_with(a,b,sign)
        self.enable_ssa('z')
        for i in range(self.num+2):
            self.z = Wire(self.widthp)

        self.enable_ssa('y')
        for i in range(self.count):
            self.y = Wire((self.enc.neg[i]**len(self.b))^self.b)
            expr = (self.y*(self.enc.lastb^self.enc.neg[i])).validif(self.enc.m1[i])
            expr|= (self.enc.neg[i]*self.y).validif(self.enc.m2[i])
            self.zs[i][2*i::len(expr)] = expr
            
            if i>0:self.zs[i][:2*i] = 0
            stop = 2*i+len(expr)
            if stop<len(self.z):
                self.zs[i][stop:] = 3 if i==0 else 2
            self.zs[-1][2*i] = self.enc.neg[i]
            if 2*i<self.widthb:
                self.zs[-1][2*i+1] = 0
        for i in range(self.num):
            loc = self.widthb+2*i
            if loc>=self.count*2:
                self.zs[-1][loc] = 0
            self.zs[-1][loc+1] = ~self.enc.ext[i]
        if not self.odd:
            self.zs[-2][-self.widthb:] = self.b.validif(self.enc.lasta)
            self.zs[-2][:-self.widthb] = 0
        self.tree = WallaceTree(self.zs)
        self.u = Wire(expr=self.tree.c,io=io)
        self.v = Wire(expr=self.tree.s,io=io)
    def expecting_lv(self):
        n = ((self.widthx)>>1)+2
        lv = 0
        while n>2:
            lv+=1
            n-=n//3
        return lv
@memorized
def get_mul_root(widtha,widthb=None):
    if widthb is None:widthb = widtha
    class mul(VModule):
        a = Wire(widtha,io='input')
        b = Wire(widthb,io='input')
        sign = Wire(1,io='input')
        res = MultiplierRoot(a,b,sign,io='output',bypass=True)
    return mul
    
