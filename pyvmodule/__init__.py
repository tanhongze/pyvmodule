__all__ = ['VModule','VStruct','Wire','Reg',
    'Mux','Concatenate','BitReduce','Reduce',
    'Hexadecimal','Decimal','Octal','Binary',
    'Always','Initial','AlwaysDelay','When',
    'Expr','clog2','cond_if',
    'expr','ast','vmodule','check',
    'tools','language']
from .vmodule import *
from .expr import *
from .vstruct import VStruct
from .tools.logic import cond_if
import sys
import os
prj_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/..')
if prj_dir not in set(sys.path):
    sys.path.insert(0,prj_dir)
def clog2(x):
    if x<=1:
        return 0
    c = 2
    n = 1
    while c<x:
        c =c<<1
        n+=1
    return n