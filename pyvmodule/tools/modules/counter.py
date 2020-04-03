from pyvmodule.wire import Reg,Wire
from pyvmodule.ctrlblk import When
from pyvmodule.tools.encodings import gray_code,gray_index
from pyvmodule.expr import Hexadecimal as Hex
from pyvmodule.tools.logic import decode,encode
class Counter(Reg):
    @property
    def sat(self):return self.saturate
    @property
    def inc_val(self):
        if self.sat:return (self+1)|(self.equal_to(-1)**len(self))
        else:return self+1 
    @property
    def dec_val(self):
        if self.sat:(self-1).validif(~self.equal_to(0))
        else:return self-1
    def __init__(self,width,reset,inc=0,dec=0,sat=False,init=0):
        Reg.__init__(self,width=width)
        self.reset = reset if isinstance(reset,Wire) else Wire(width=1,expr=reset)
        self.inc_cond  = inc
        self.dec_cond  = dec
        self.init_val  = init
        self.saturate  = sat
        self._init()
        self._init_end()
    def _init(self):pass
    def _init_end(self):
        inc = self.inc_cond&~self.dec_cond
        dec = self.dec_cond&~self.inc_cond
        self.we = inc|dec
        if not (self.we is inc or self.we is dec):self.we = Wire(self.we)
        val = 0
        if self.inc_cond != 0:val|=self.inc_val.validif(inc)
        if self.dec_cond != 0:val|=self.dec_val.validif(dec)
        self.next = Wire(width=len(self),expr=val)
        self[:] = When(self.reset)[self.init_val].When(self.we)[self.next]
class GrayCounter(Counter):
    @property
    def inc_val(self):return self.gray_next
    @property
    def dec_val(self):return self.gray_prev
    def _init(self):
        numwin = 1<<len(self)
        self.dec = decode(self)
        self.gray_next = encode(self.dec,logic=lambda i:gray_code(gray_index(i)+1))
        self.gray_prev = encode(self.dec,logic=lambda i:gray_code((gray_index(i)+numwin-1)%numwin))
    