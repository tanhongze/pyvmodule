from .logic import *
from vmodule import *
class GrayCode:
    codes = [0]
    prevs = [None]
    nexts = [None]
    max_width = 0
    indexes = [0]
    @classmethod
    def extend(cls,width):
        if cls.max_width>=width:
            return
        for i in range(cls.max_width,width):
            cls.nexts[-1] = i
            codes = []
            nexts = []
            prevs = []
            indexes = []
            num = len(cls.codes)
            for j in range(num-1,-1,-1):
                codes.append(cls.codes[j]^(1<<i))
                nexts.append(cls.prevs[j])
                prevs.append(cls.nexts[j])
            for j in range(num):
                indexes.append((2<<i)-1-cls.indexes[j])
            cls.codes.extend(codes)
            cls.nexts.extend(nexts)
            cls.prevs.extend(prevs)
            cls.indexes.extend(indexes)
        assert len(cls.codes)==(1<<width)
        cls.max_width = width
        return GrayCode
    def __init__(self,width=1,ring=False,combinational=True,next=True,prev=True):
        if width<=0:
            raise RuntimeError('Invalid negative width.')
        self.width=width
        self.next = next
        self.prev = prev
        self.ring = ring
        self.combinational = combinational
        self.extend(self.width)
    def implemtent(self):
        class GrayCodeCounter(VModule):
            if self.combinational:
                counter = Wire(io='input')
                counter_next = Wire(io='output')
            else:
                clock = Wire(io='input')
                reset = Wire(io='input')
                counter = Reg(io='output')
                counter_next = Wire()
            if self.next:
                next_valid = Wire(io='input')
            else:
                next_valid = None
            if self.prev:
                prev_valid = Wire(io='input')
            else:
                prev_valid = None
            self.connect(counter_next,counter,next_valid,prev_valid,ring=self.ring)
        return GrayCodeCounter
    @classmethod
    def connect(cls,counter_next,counter,next_valid=None,prev_valid=None,ring=False):
        cls.extend(len(counter))
        # a^(a&b1|a&b2|~a&c1|~a&c2) = a&~b1&~b2|(~a&c1|~a&c2)
        pos_exprs = []
        neg_exprs = []
        for i in range(len(counter)):
            pos_exprs.append(0)
            neg_exprs.append(counter[i])
            
        def append_expr(counter,code,index,valid,pos_exprs,neg_exprs):
            conds = bit_eq_const(counter,code)
            conds.pop(index)
            conds.append(valid)
            if (code>>index)&1:
                neg_exprs[index] = neg_exprs[index]&~Reduce('&',conds)
            else:
                pos_exprs[index] = pos_exprs[index]|~counter[index]&Reduce('&',conds)
        for i in range(1<<len(counter)):
            next = cls.nexts[i]
            prev = cls.prevs[i]
            code = cls.codes[i]
            if next!=None and next_valid!=None:
                append_expr(counter,code,next,next_valid,pos_exprs,neg_exprs)
            if prev!=None and prev_valid!=None:
                append_expr(counter,code,prev,prev_valid,pos_exprs,neg_exprs)
        if ring or prev_valid==None or next_valid==None:
            if next_valid!=None:
                next = len(counter)-1
                code = cls.codes[-1]
                append_expr(counter,code,next,next_valid,pos_exprs,neg_exprs)
            if prev_valid!=None:
                prev = len(counter)-1
                code = cls.codes[0]
                append_expr(counter,code,prev,prev_valid,pos_exprs,neg_exprs)
        for i in range(len(counter)):
            counter_next[i] = neg_exprs[i]|pos_exprs[i]
        