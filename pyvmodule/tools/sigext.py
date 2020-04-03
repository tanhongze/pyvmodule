__all__ = ['ZeroExt','OneExt','SignExt','CutOut']
from pyvmodule.ast import ASTNode
from pyvmodule.expr import Hexadecimal as Hex
errstr_narrowed = 'Called to extending signal "%s" (width=%d) to narrowed width %d.'
errstr_widened = 'Called to cutting out signal "%s" (width=%d) to widened width %d.'
def Error(errstr,expr,width):
    return ValueError(errstr_narrowed%(str(expr),len(expr),width))
def XXXXExt(expr,width,cut=False,func=None):
    if isinstance(width,ASTNode):width = len(width)
    if len(expr)<width:return func(expr,width)
    elif len(expr)==width:return expr
    elif cut:return expr[:width]
    else:raise Error(errstr_narrowed,expr,width)
zero_ext_func = lambda expr,width:expr*Hex(0,width=width-len(expr))
sign_ext_func = lambda expr,width:expr*(expr[-1]**(width-len(expr)))
one_ext_func  = lambda expr,width:expr*Hex(-1,width=width-len(expr))
def ZeroExt(*arg,**kwargs):
    return XXXXExt(*arg,**kwargs,func=zero_ext_func)
def SignExt(*arg,**kwargs):
    return XXXXExt(*arg,**kwargs,func=sign_ext_func)
def OneExt(*arg,**kwargs):
    return XXXXExt(*arg,**kwargs,func=one_ext_func)
def CutOut(expr,width):
    if isinstance(width,ASTNode):width = len(width)
    if len(expr)>=width:return expr[:width]
    else:raise Error(errstr_widened,expr,width)
    