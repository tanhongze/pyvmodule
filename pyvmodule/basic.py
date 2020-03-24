from .vmodule import VModule
from .expr import Expr,Binary,Octal,Hexadecimal,Concatenate
from .ctrlblk import When,Always,Initial,AlwaysDelay
from .vstruct import VStruct
from . import vfunction
from .wire import Wire,Reg
Hex = Hexadecimal
clog2 = vfunction.clog2