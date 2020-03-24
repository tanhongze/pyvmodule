from .ast import ASTNode
from .tools.utility import clog2 as clog2_math
class VFunction(ASTNode):
    @property
    def typename(self):return 'function'
    @property
    def name(self):return self._name
    @name.setter
    def name(self,name):self._name = name
    def __init__(self,name,*args):
        self.name = name
        self.args = args
    def _generate(self,indent=0):
        contents = [[' '*indent,'$',self.name]]
        if len(self.args)==0:return contents
        contents[-1].append('(')
        contents[-1].extend(('"%s"'%arg if isinstance(arg,str) else str(arg)) for arg in self.args)
        contents[-1].append(')')
        return contents
def display   (*args ):return VFunction('display',*args)
def monitor   (*args ):return VFunction('monitor',*args)
def strobe    (*args ):return VFunction('strobe' ,*args)
def write     (*args ):return VFunction('write'  ,*args)
def fopen     (*args ):return VFunction('fopen'  ,*args)
def fclose    (*args ):return VFunction('fclose' ,*args)
def monitoron (      ):return VFunction('monitoron')
def monitoroff(      ):return VFunction('monitoroff')
def time      (      ):return VFunction('time')
def stime     (      ):return VFunction('stime')
def realtime  (      ):return VFunction('realtime')
def stop      (n=None):return VFunction('stop') if n is None else VFunction('stop',n)
def finish    (n=None):return VFunction('finish') if n is None else VFunction('finish',n)
def readmemb  (*args ):return VFunction('readmemb',*args)
def readmemh  (*args ):return VFunction('readmemh',*args)
def random    (      ):return VFunction('random')
def timeformat(*args ):return VFunction('timeformat',*args)
def printtimescale(*args):return VFunction('printtimescale',*args)
def realtobits(*args):return VFunction('realtobits',*args)
def bitstoreal(*args):return VFunction('bitstoreal',*args)
def rtoi      (*args):return VFunction('rtoi',*args)
def itor      (*args):return VFunction('itor',*args)
def dumpfile  (fname):return VFunction('dumpfile',fname)
def dumpvars  (*args):return VFunction('dumpvars',*args)
def dumpoff   (*args):return VFunction('dumpoff',*args)
def dumpon    (*args):return VFunction('dumpon',*args)
def dumpall   (*args):return VFunction('dumpall',*args)
def dumplimit (*args):return VFunction('dumplimit',*args)
def dumpflush (*args):return VFunction('dumpflush',*args)

def clog2(x,dynamic=False):
    if isinstance(x,ASTNode) and x.typename=='const':x = int(x)
    if isinstance(x,int):return clog2_math(x)
    if dynamic:return VFunction('dumplimit',x)
    else:raise TypeError('Math function "clog2" excepts constant input, use "clog2(x,dynamic=True)" to enable dynamic $clog2 function in verilog.')
    
    
