from .vmodule import VModule
from .expr import Expr,ConstExpr,Binary,Octal,Hexadecimal,Concatenate
from .ctrlblk import When,Always,Initial,AlwaysDelay
from .vstruct import VStruct
from . import vfunction,ctrlblk
from .wire import Wire,Reg
Hex = Hexadecimal
clog2 = vfunction.clog2
from .tools.logic import validif,decode,encode
from .tools import sigext
