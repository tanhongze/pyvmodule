def cond_if(cond,value):
    if isinstance(cond,(int,bool)):
        return value if cond else 0
    if isinstance(value,int) and value==0:
        return 0
    return (cond**len(value))&value
def vrange(step,count,start=None,stop=None):
    if stop==None:
        stop = count*step
    if start==None:
        start = 0
    for i in range(count):
        yield i,slice(start+i*step,min(start+i*step+step,stop))
    return
def decode(enc):
    dec = type(enc)(1<<len(enc))
    for i in range(1<<len(enc)):
        dec[i] = enc//i
    return dec