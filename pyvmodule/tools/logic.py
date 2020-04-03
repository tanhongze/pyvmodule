__all__ = [
    'validif',
    'decode','encode',
    'BitReduce']
from pyvmodule.wire import Wire
from pyvmodule.expr import Binary,Hexadecimal
from pyvmodule.vfunction import clog2
def validif(cond,value):
    if isinstance(cond,(int,bool)):return value if cond else 0
    if isinstance(value,int):return Hexadecimal(value).validif(cond)
    return value.validif(cond)
def decode(enc,width=None,logic=lambda a,b:a//b):
    dec = Wire(1<<len(enc) if width is None else width)
    for i in range(len(dec)):
        dec[i] = logic(enc,i)
    return dec
def encode(dec,width=None,logic=lambda i:i):
    if width is None:width = clog2(len(dec))
    enc = 0
    for i in range(len(dec)):
        enc|= Hexadecimal(logic(i),width=width).validif(dec[i])
    return Wire(enc)
bitreduce_operators = {'|':' |',' |':' |','&':' &',' &':' &','^':' ^',' ^':' ^'}
bitreduce_identities= {' |':Binary(0,width=1),' ^':Binary(0,width=1),'&':Binary(1,width=1)}
def BitReduce(typename,expr):
    if typename not in bitreduce_operators:
        raise RuntimeError('Unexpected bitwise-reduction operator "%s".'%typename)
    typename = bitreduce_operators[typename]
    if isinstance(expr,list):
        if len(expr)==0:
            return bitreduce_identities[typename]
        if len(expr)==1:
            return BitReduce(typename,expr[0])
        expr = Concatenate(expr)
    if len(expr)==1:return expr
    else:return UnaryOperator(typename,expr)