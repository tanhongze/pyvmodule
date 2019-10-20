from vmodule import Reduce
from vmodule import Wire
from vmodule import Concatenate
from vmodule import Always
from vmodule import When
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
def cond_if(cond,value):
    return (cond**len(value))&value
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