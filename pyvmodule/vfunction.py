from .ast import ASTNode
from .tools.utility import clog2 as clog2_math
class VFunction(ASTNode):
    @property
    def typename(self):return 'function'
    @property
    def name(self):return self._name
    @name.setter
    def name(self,name):self._name = name
    def __init__(self,name,*args,cond=None,delay=None):
        self.name = name
        self.args = args
        self.cond = cond
        self.delay = delay
    def _generate(self,indent=0):
        contents = []
        if not self.delay is None:
            contents.append([' '*indent,'#',str(self.delay)])
        if not self.cond is None:
            contents.append([' '*indent,'if','(',str(self.cond),')'])
            contents.append([' '*indent,'begin'])
        contents.append([' '*(indent if self.cond is None else indent+4),'$',self.name])
        if len(self.args)==0:return contents
        contents[-1].append('(')
        contents[-1].append(','.join([('"%s"'%arg if isinstance(arg,str) else str(arg)) for arg in self.args]))
        contents[-1].append(')')
        if not self.cond is None:
            contents.append([' '*indent,'end'])
        return contents
def display   (*args,**kwargs):return VFunction('display',*args,**kwargs)
def monitor   (*args,**kwargs):return VFunction('monitor',*args,**kwargs)
def strobe    (*args,**kwargs):return VFunction('strobe' ,*args,**kwargs)
def write     (*args,**kwargs):return VFunction('write'  ,*args,**kwargs)
def fopen     (*args,**kwargs):return VFunction('fopen'  ,*args,**kwargs)
def fclose    (*args,**kwargs):return VFunction('fclose' ,*args,**kwargs)
def monitoron (      **kwargs):return VFunction('monitoron',**kwargs)
def monitoroff(      **kwargs):return VFunction('monitoroff',**kwargs)
def time      (      **kwargs):return VFunction('time',**kwargs)
def stime     (      **kwargs):return VFunction('stime',**kwargs)
def realtime  (      **kwargs):return VFunction('realtime',**kwargs)
def stop      (n=None,**kwargs):return VFunction('stop',**kwargs) if n is None else VFunction('stop',n,**kwargs)
def finish    (n=None,**kwargs):return VFunction('finish',**kwargs) if n is None else VFunction('finish',n,**kwargs)
def readmemb  (*args,**kwargs):return VFunction('readmemb',*args,**kwargs)
def readmemh  (*args,**kwargs):return VFunction('readmemh',*args,**kwargs)
def random    (      **kwargs):return VFunction('random',**kwargs)
def timeformat(*args,**kwargs):return VFunction('timeformat',*args,**kwargs)
def printtimescale(*args,**kwargs):return VFunction('printtimescale',*args,**kwargs)
def realtobits(*args,**kwargs):return VFunction('realtobits',*args,**kwargs)
def bitstoreal(*args,**kwargs):return VFunction('bitstoreal',*args,**kwargs)
def rtoi      (*args,**kwargs):return VFunction('rtoi',*args,**kwargs)
def itor      (*args,**kwargs):return VFunction('itor',*args,**kwargs)
def dumpfile  (fname,**kwargs):return VFunction('dumpfile',fname,**kwargs)
def dumpvars  (*args,**kwargs):return VFunction('dumpvars',*args,**kwargs)
def dumpoff   (*args,**kwargs):return VFunction('dumpoff',*args,**kwargs)
def dumpon    (*args,**kwargs):return VFunction('dumpon',*args,**kwargs)
def dumpall   (*args,**kwargs):return VFunction('dumpall',*args,**kwargs)
def dumplimit (*args,**kwargs):return VFunction('dumplimit',*args,**kwargs)
def dumpflush (*args,**kwargs):return VFunction('dumpflush',*args,**kwargs)

def clog2(x,dynamic=False):
    if isinstance(x,ASTNode) and x.typename=='const':x = int(x)
    if isinstance(x,int):return clog2_math(x)
    if dynamic:return VFunction('dumplimit',x)
    else:raise TypeError('Math function "clog2" excepts constant input, use "clog2(x,dynamic=True)" to enable dynamic $clog2 function in verilog.')
    
    
