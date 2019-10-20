from vmodule import *
from .comments import SynopsysComments as snp
from .logic import bit_eq_const
from .logic import cross_decode
class Decoder:
    def __init__(self,n,m,base=0):
        self.n = n
        self.m = m
        self.base = base
    @classmethod
    def connect_set(cls,code,s,name=None):
        if not isinstance(code,list):
            code = [code[i] for i in range(len(code))]
        
        if name==None:
            if isinstance(code,Wire):
                name = code.name
            else:
                name = 'code'
            
        if len(code)<=3:
            map = {}
            code_dec = VList()
            for c in s:
                dec = Wire(bit_eq_const(code,c))
                code_dec.append(dec,name=name+'_dec_%d'%c)
                map[c] = dec
            return code_dec,map
        if len(code)>3:
            m = len(code)>>1
            set_hi = set()
            set_lo = set()
            for c in s:
                set_hi.add(c>>m)
                set_lo.add(c&((1<<m)-1))
            code_hi,map_hi = connect_set(code[m:],set_hi,name=name+'_hi')
            code_lo,map_lo = connect_set(code[:m],set_lo,name=name+'_lo')
            
            code_dec = VList()
            for c in s:
                c_hi = c>>m
                c_lo = c&((1<<m)-1)
                dec = Wire(map_hi[c_hi]&map_lo[c_lo])
                code_dec.append(dec,name=name+'_dec_%d'%c)
                map[c] = dec
            code_dec.append(code_hi)
            code_dec.append(code_lo)
            return code_dec
    @classmethod
    def extract_ranges(cls):
        ranges = []
        remain = len(s)
        while remain>0:
            for i in range(start,1<<n):
                if i in s:break
            start = i
            for i in range(start,1<<n):
                if i not in s:break
            stop = i
            ranges.append((start,stop))
            start = stop
        return ranges
    @classmethod
    def connect(cls,code,start,stop=None,name=None):
        if stop==None:
            stop = start
            start = 0
        assert start< stop
        assert stop<=(1<<len(code))
        if name==None:
            if isinstance(code,Wire):
                name = code.name
            else:
                name = 'code'
        if not isinstance(code,list):
            code = [code[i] for i in range(len(code))]
        if len(code)<=3 or len(code_dec)<8:
            code_dec = Wire(stop-start,name=name+'_dec_%d_%d'%(start,stop))
            for i in range(len(code_dec)):
                j = start+i
                code_dec[i] = bit_eq_const(code,j)
            code_dec = VList([code_dec])
            return code_dec
        else:
            m = len(code)>>1
            code_hi = cls.connect(code[m:],start>>m,((stop-1)>>m)+1,name=name+'_hi')
            code_lo = cls.connect(code[:m],0,1<<m,name=name+'_lo')
            code_dec = Wire(stop-start)
            for i in range(len(code_dec)):
                j = start+i
                code_dec[i] = code_hi[0][(j>>m)-(start>>m)]&code_lo[j%(1<<m)]
            code_dec = VList([code_dec])
            code_dec.extend(code_lo)
            code_dec.extend(code_hi)
            return code_dec
    def implement(self):
        class decoder(VModule):
            if self.base==0:
                name = 'decoder_%d_%d'%(self.n,self.m)
            else:
                name = 'decoder_%d_%d_%d'%(self.n,self.base,self.m)
            code = Wire(self.n,io='input')
            code_dec = self.connect(code,self.base,self.m-self.base)
            code_dec[0].io='output'
        return decoder