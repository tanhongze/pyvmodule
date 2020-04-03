import sys
import os
vmodule_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../..')
cur_path =  set(sys.path)
if vmodule_dir not in cur_path:
    sys.path.insert(0,vmodule_dir)
from pyvmodule.develope import *
from pyvmodule.tools.logic import decode
class TestAlways(VModule):
    clock = Wire(io='input')
    reset = Wire(io='input')
    x = Wire(io='input')
    sel = Wire(io='input')
    beta = Reg(io='output')
    alpha = Reg(io='output')
    blk =  When(reset)[alpha:0][beta:0].Otherwise[When(sel)[beta:x].Otherwise[alpha:x]]
TestAlways.save()
class Counter(VModule):
    comments.append('example001 -- a simple counter.')
    clock = Wire(io='input')
    reset = Wire(io='input')
    valid = Wire(io='input')
    valid.comments.append('Enable signal for counter.')
    cnt = Reg(4,io='output')
    cnt_next = Wire(cnt+1)
    when_ok = When(valid)[cnt_next]
    #cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
    cnt[:] = When(reset)[0].Otherwise[when_ok]
Counter.save()
def get_counter(width):
    class Counter(VModule):
        name = 'counter_%d'%width
        comments.append('example002 -- a simple counter.')
        clock = Wire(io='input')
        reset = Wire(io='input')
        valid = Wire(io='input')
        valid.comments.append('Enable signal for counter.')
        cnt = Reg(width,io='output')
        cnt_next = Wire(cnt+1)
        
        when_ok = When(valid)[cnt_next]
        cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
    return Counter
class CounterConstructor:
    def __init__(self,width=4,valid=True):
        self.width = width
        self.valid = valid
        self.name = 'counter_%d'%width+('_valid')
    def add_one(self,value):
        return Wire(value+1)
    def implement(self):
        class Counter(VModule):
            name = self.name
            comments.append('example002 -- a simple counter.')
            clock = Wire(io='input')
            reset = Wire(io='input')
            cnt = Reg(self.width)
            cnt.next = self.add_one(cnt)
            cnt.io='output'
            if self.valid:
                valid = Wire(io='input')
                valid.comments.append('Enable signal for counter.')
                when_ok = When(valid)[cnt_next]
            else:
                valid = 1
                when_ok = cnt_next
            cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
        return Counter
class Decoder(VModule):
    di = Wire(5,io='input')
    do = decode(di)
    do.io = 'output'
if __name__ == '__main__':
    Decoder.save()
    get_counter(5).save()