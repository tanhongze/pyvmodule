def count_one32(x):
    y = (x&0x55555555)+((x>>1)&0x55555555)
    x = (y&0x33333333)+((y>>2)&0x33333333)
    y = (x&0x0f0f0f0f)+((x>>4)&0x0f0f0f0f)
    x = (y+(y>>8 ))&0x00ff00ff
    y = (x+(x>>8 ))&0x0000ffff
    return y
def count_one(x):
    if x<0:raise ValueError('Cannot count the number 1 in negative number.')
    n = 0
    while x>0:
        n+=count_one32(x)
        x>>=32
    return n
def clog2(x):
    if x<=1:return 0
    c = 2
    n = 1
    while c<x:
        c =c<<1
        n+=1
    return n
