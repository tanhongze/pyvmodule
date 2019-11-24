from vmodule import *
class TestBench(VModule):
    clock = Reg()
    reset = Reg()
    timer = Reg(32)
    clock[:] = Initial(0).Next(AlwaysDelay(5)[~clock])
    timer[:] = Initial(0).Next(Always(clock)[timer+1])
    reset[:] = Initial(1).Next(Always(clock)[When(timer//10)[0]])