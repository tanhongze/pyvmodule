import sys
import os
vmodule_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../..')
cur_path =  set(sys.path)
if vmodule_dir not in cur_path:
    sys.path.insert(0,vmodule_dir)
from vmodule import *
class Counter(VModule):
    comments.append('example001 -- a simple counter.')
    clock = Wire(io='input')
    reset = Wire(io='input')
    valid = Wire(io='input')
    valid.comments.append('Enable signal for counter.')
    cnt = Reg(4,io='output')
    cnt_next = Wire(cnt+1)
    
    when_ok = When(valid)[cnt_next]
    cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
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
    def add_one(self,cnt_next,cnt):
        cnt_next[:] = cnt+1
    def implement(self):
        class Counter(VModule):
            name = self.name
            comments.append('example002 -- a simple counter.')
            clock = Wire(io='input')
            reset = Wire(io='input')
            cnt = Reg(self.width,io='output')
            cnt_next = Wire(self.width)
            self.add_one(cnt_next,cnt)
            
            if self.valid:
                valid = Wire(io='input')
                valid.comments.append('Enable signal for counter.')
                when_ok = When(valid)[cnt_next]
            else:
                valid = 1
                when_ok = cnt_next
            cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
        return Counter
if __name__ == '__main__':
    Counter.save(dir=sys.stdout)
    get_counter(5).save(dir=sys.stdout)
    CounterConstructor(width=3,valid=False).implement().save(dir=sys.stdout)