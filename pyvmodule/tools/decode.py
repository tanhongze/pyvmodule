from vmodule import *
from .comments import SynopsysComments as snp
from .logic import cond_if
def bit_xor_const(code,value):
    retval = []
    for i in range(len(code)):
        if (value>>i)&1:
            retval.append(~code[i])
        else:
            retval.append(+code[i])
    return retval
def bit_eq_const(code,value):
    retval = []
    for i in range(len(code)):
        if (value>>i)&1:
            retval.append(+code[i])
        else:
            retval.append(~code[i])
    return retval
def bit_extract(code,*args):
    if len(args)<=0:
        args = (len(code),)
    if len(args)>3:
        raise TypeError('Too many arguments.')
    return [code[i] for i in range(*args)]
def cross_decode(code,*args):
    if len(args)<=0:
        args = (len(code),)
    if len(args)>3:
        raise TypeError('Too many arguments.')
    to_dec = bit_extract(code,*args)
    high = Wire(bit_decode(to_dec[len(to_dec)>>1:]),name='h')
    low = Wire(bit_decode(to_dec[:len(to_dec)>>1]),name='l')
    dec = Wire(bit_tensor(low,high),name='dec')
    return [dec,low,high]
def bit_decode(code,*args):
    if len(args)<=0:
        args = (len(code),)
    if len(args)>3:
        raise TypeError('Too many arguments.')
    to_dec = bit_extract(code,*args)
    return Concatenate([Reduce('&',bit_eq_const(to_dec,i)) for i in range(1<<len(to_dec))])
def bit_tensor(low,high,*args):
    if len(args)==0:
        start = 0
        stop = len(high)
    elif len(args)==1:
        start = 0
        stop = args[0]
    elif len(args)==2:
        start = args[0]
        stop = args[1]
    else:
        raise TypeError('Too many arguments.')
    exprs = []
    for i in range(start,stop):
        exprs.append(cond_if(high[i],low))
    return Concatenate(exprs)
class Decoder:
    @property
    def m(self):
        return 1<<self.n
    def __init__(self,n,fan_in=3):
        self.n = n
        self.fan_in = fan_in
    def prepare_base(self):
        return [[~code[i],code[i]] for i in range(len(code))]
    @classmethod
    def tersor(self,depth,A,B):
        if depth<=1:
            return A
        else:
            R = []
            B = B[0]
            for i in range(len(B)):
                b = B[i]
                if isinstance(A,list):
                    for a in A:
                        Rs.append(cond_if(b,a))
                else:
                    Rs.append(cond_if(b,A))
                    
            return self.tensor(depth-1,R,B[1:])
    def merge_decode(self,decoding):
        if len(decoding)<=1:
            return decoding
        else:
            decoded = VStruct(('sub',,))
            for i in range(0,len(decoding),self.fan_in):
                setattr(decoded,'sub_%d',self.tensor(min(i+self.fan_in,len(decoding))decoding[0],decoding[1:])))
            dec = [[code_dec[i] for i in range(len(code_dec))] for code_dec in decoded]
            decoded.dec = self.merge_decode()
            return decoded
    def implement(self):
        class decoder(VModule):
            name = 'decoder_%d_%d'%(self.n,self.m)
            code = Wire(self.n,io='input')
            subcode = self.merge_decode(self.prepare_base(code))
            code_dec = Wire(self.m,io='output')
            code_dec[:] = subcode.dec
        return decoder