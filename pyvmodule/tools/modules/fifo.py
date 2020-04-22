from pyvmodule.develope import *
def a_eq_b_add_1(a,b):
    eq = Wire()
    eq.comments.append('%s == %s + 1'%(str(a),str(b)))
    eq.s = Wire(len(a))
    eq.c = Wire(len(a)-1)
    eq.s[0]  = ~(~a[0]^b[0])
    eq.c[0]  = (~a[0]|b[0])
    eq.s[1:] = ~a[1:]^b[1:]
    eq.c[1:] = ~a[1:]&b[1:]
    eq[:]    = s[0]&(s[1:]^c).reduce_and()
    return eq
class FifoQueue(VStruct):
    def __init__(self,reset,push,pop,data,depth=2,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.full  = Wire()
        self.empty = Wire()
        self.reset = reset
        self.push = Wire(push&~self.full )
        self.pop  = Wire(pop &~self.empty)
        self.push.data = data
        self.depth = depth
        
        self.valid = Reg()
        self.datas = Reg(width=len(data),length=1<<depth)

        if depth >  0:
            self.head  = Reg (width=depth)
            self.tail  = Reg (width=depth)
            self.boundary[:] = Wire(self.head.equal_to(self.tail))
            When(reset)[self.tail:0].When(self.pop )[self.tail:self.tail+1]
            When(reset)[self.head:0].When(self.push)[self.head:self.head+1]
            When(self.push)[self.datas[self.head]:self.push.data]
            self.data = Wire(self.queue[self.tail])
            #self.tail.near = Wire(self.head.equal_to(self.tail+1))
            self.tail.near = a_eq_b_add_1(self.head,self.tail,1)
            When(reset)[self.valid:0]\
            .When(self.push)[self.valid:1]\
            .When(self.pop)[self.valid:self.tail.near]
        else:
            self.boundary = Binary(1,width=1)
            self.data = self.datas
            When(reset)[self.valid:0]\
            .When(self.push)[self.valid:1]\
            .When(self.pop)[self.valid:0]
            When(self.push)[self.datas:self.push.data]

        self.full [:] = self.boundary& self.valid
        self.empty[:] = self.boundary&~self.valid
class Fifo(VStruct):
    @staticmethod
    def extract(bus,names):
        data = None
        for name in names:
            data*= getattr(bus,name)
        return data
    @property
    def empty(self):return ~self.valid
    def __init__(self,reset,source,push=None,pop=None,names=None,depth=0,**kwargs):
        VStruct.__init__(self,**kwargs)
        self.names = names
        self.depth = depth
        self.reset = reset
        self.valid = Reg()
        self.full  = Wire()
        self.push  = Wire() if push is None else Wire(push&~self.full)
        self.pop   = Wire() if pop  is None else Wire(pop &self.valid)

        if names is None:self.push.data = source
        else:self.push.data = Wire(self.extract(source,names))

        if self.depth>=0:
            self.queue = FifoQueue(reset,self.push&self.valid,self.pop,self.push.data,depth=depth)
            self.full[:] = self.queue.full
            self.valid[:]=When(reset)[0]\
            .When(self.push)[1]\
            .When(self.pop)[self.queue.valid]
            if names is None:
                self.data = Reg(width=len(self.push.data))
                self.data.push = Wire(self.push&~self.valid)
                When(self.data.push)[self.data:self.push.data]\
                .When(self.pop)[self.data:self.queue.data]
            else:
                for name in names:
                    setattr(self.queue.data,name,Wire(width=len(getattr(source,name))))
                self.extract(self.queue.data,names)[:] = self.queue.data

                self.data = Wire(width=len(self.push.data))
                for name in names:
                    setattr(self.data,name,Reg(width=len(getattr(source,name))))
                self.data [:]= self.extract(self.data,names)
                self.data.push = Wire(self.push&~self.valid)

                blk = When(self.data.push)
                for name in names:
                    if hasattr(self,'update_data_'+name):continue
                    blk[getattr(self.data,name):getattr(source,name)]
                blk = blk.When(self.pop)
                for name in names:
                    if hasattr(self,'update_data_'+name):continue
                    blk[getattr(self.data,name):getattr(self.queue.data,name)]

                for name in names:
                    if not hasattr(self,'update_data_'+name):continue
                    blk = When(self.data.push)[getattr(self.data,name):getattr(source,name)]
                    blk = blk.When(self.pop)[getattr(self.data,name):getattr(self.queue.data,name)]
                    blk.Otherwise[getattr(self,'update_data_'+name)(getattr(self.data,name))]
        else:raise NotImplementedError()


class FifoPort(VStruct):
    def __init__(self,*args,T=Wire,io='auto',**kwargs):
        VStruct.__init__(self,**kwargs)
        self.valid = Wire(io=io)
        self.ready = Wire(io=io)
        self.data  = T(*args,io=io)
if __name__ == '__main__':
    class demo(VModule):
        clock = Wire(io='input')
        reset = Wire(io='input')
        i = FifoPort(32,io='auto')
        o = FifoPort(32,io='auto')
        fifo = Fifo(reset,i.data,push=i.valid,pop=o.ready,depth=0)
        o.data [:] = fifo.data
        o.valid[:] = fifo.valid
        i.ready[:] =~fifo.full
    print(str(demo))
