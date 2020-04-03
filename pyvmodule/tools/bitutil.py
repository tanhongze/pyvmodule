from pyvmodule.basic import *
from collections import defaultdict
def divexp(n,i):
    return (n>>i)+(1 if (((1<<i)-1)&n) != 0 else 0)
def divexp1(n):
    return (n>>1)+(n&1)

def keep(sig):return sig
def invert(sig):return ~sig
def redu0(sig):return sig
def redu1(sig):return sig.reduce_and()

def make_exist(sig,io=None):
    exist = Wire(io=io)
    i = 0
    exist.enable_ssa('lv')
    exist.lv = sig
    num   = len(sig)
    while num>1:
        width = divexp1(num)
        lv = Wire(width)
        for j in range(num>>1):
            lv[j] = exist.lv[2*j::2].reduce_or()
        if num&1:lv[-1] = exist.lv[-1]
        exist.lv = lv
        num = width
    exist[:] = exist.lvs[-1]
    return exist

def _last_sel(exist,j,codes):return exist[2*j+1].mux(codes[2*j+1],codes[2*j])
def _last_enc(exist,j):return exist[2*j+1]
def _first_sel(exist,j,codes):return exist[2*j].mux(codes[2*j],codes[2*j+1])
def _first_enc(exist,j):return ~exist[2*j]
def _make_fst_lst(exist,_sel,_enc,io=None):
    num = len(exist.lvs[0])
    if num<=1:return None
    enc = Wire(clog2(num),io=io)
    enc.enable_ssa('lv')
    enc.lv = VStruct()
    
    enc.lv.codes = Wire(len(exist.lv1))
    for j in range(num>>1):
        enc.lv.codes[j] = _enc(exist.lv0,j)
    if num&1:enc.lv.codes[-1] = 0
    
    num   = len(enc.lv.codes)
    width = 2
    while num>1:
        lv = VStruct()
        lv.enable_ssa('code')
        elv = exist.lvs[width-1]
        for j in range(num>>1):
            lv.code = Wire(width)
            codes = enc.lv.codes
            lv.code[:-1] = _sel(elv,j,codes)
            lv.code[ -1] = _enc(elv,j)
        if num&1:lv.code = Wire(sigext.ZeroExt(enc.lv.code,width+1))
        enc.lv = lv
        num   = len(enc.lv.codes)
        width += 1
    enc[:] = enc.lv.code
    return enc
def _make_sel(exist,sources,_sel,io=None):
    num = len(exist.lvs[0])
    if num==1:return sources[0]
    if len(sources)!=num:raise ValueError('Count of entries (%d) is mis-matched with count of valid signals (%d).'%(len(sources),num))
    sel = Wire(len(sources[0]))
    sel.enable_ssa('lv')
    sel.lv = VStruct()
    sel.lv.srcs = sources
    
    i = 0
    while num>1:
        lv = VStruct()
        lv.enable_ssa('src')
        elv = exist.lvs[i]
        for j in range(num>>1):
            lv.src = Wire(_sel(elv,j,sel.lv.srcs))
        if num&1:lv.src = sel.lv.src
        sel.lv = lv
        num   = len(sel.lv.srcs)
        i += 1
    sel[:] = sel.lv.src
    return sel

def make_sel_first(exist,sources,**kwargs):return _make_sel(exist,sources,_first_sel,**kwargs)
def make_sel_last (exist,sources,**kwargs):return _make_sel(exist,sources,_last_sel ,**kwargs)
    
def make_last  (exist,**kwargs):return _make_fst_lst(exist,_last_sel ,_last_enc ,**kwargs)
def make_first (exist,**kwargs):return _make_fst_lst(exist,_first_sel,_first_enc,**kwargs)

def make_onehot(exist,io=None):
    enc = Wire(clog2(len(exist.lvs[0])),io=io)
    for i in range(len(enc)):
        expr = 0
        elv = exist.lvs[i]
        for j in range(1,len(elv),2):
            expr|= elv[j]
        enc[i] = expr
    return enc

def make_mask_gx_first(exist,res,eq,io=None):
    mask = Wire(len(exist.lvs[0]),io=io)
    for i in range(len(mask)):
        # [l=0,r)
        r = i + eq
        k = 0
        cur = r
        pivots = []
        levels = []
        while cur>0:
            if (cur>>k)&1:
                cur -= (1<<k)
                pivots.append(cur>>k)
                levels.append(k)
            k+=1
        expr = 0
        for j in range(len(pivots)):
            expr|=exist.lvs[levels[j]][pivots[j]]
        mask[i] = res(expr)
    return mask
    
def make_mask_gt_first(exist,io=None):return make_mask_gx_first(exist,keep  ,0,io=io)
def make_mask_ge_first(exist,io=None):return make_mask_gx_first(exist,keep  ,1,io=io)
def make_mask_lt_first(exist,io=None):return make_mask_gx_first(exist,invert,1,io=io)
def make_mask_le_first(exist,io=None):return make_mask_gx_first(exist,invert,0,io=io)

def make_mask_lx_last(exist,res,ne,io=None):
    mask  = Wire(len(exist.lvs[0]),io=io)
    r     = len(mask)
    for i in range(r):
        # [l,r)
        l = i + ne
        x = r&~l
        j = 0
        while (x>>j)>0:
            j+=1
        j-= 1
        if j<0:
            mask[i] = 0
            continue
        k = 0
        cur = l
        pivots = []
        levels = []
        while cur < r:
            if (cur>>k)&1 or k==j:
                pivots.append(cur>>k)
                levels.append(k)
                cur += (1<<k)
            k += 1
        expr = 0
        for j in range(len(pivots)):
            expr|=exist.lvs[levels[j]][pivots[j]]
        mask[i] = res(expr)
    return mask
    
def make_mask_gt_last(exist,io=None):return make_mask_lx_last(exist,invert,1,io=io)
def make_mask_ge_last(exist,io=None):return make_mask_lx_last(exist,invert,0,io=io)
def make_mask_lt_last(exist,io=None):return make_mask_lx_last(exist,keep  ,1,io=io)
def make_mask_le_last(exist,io=None):return make_mask_lx_last(exist,keep  ,0,io=io)
def reuse_invert(sig,name):return Wire(~getattr(sig,name))

d = vars()
targets1 = [
    ('exist' ,[]),
    ('first' ,[]),
    ('last'  ,[]),
    ('onehot',[]),
    ('mask_ge_first',[]),
    ('mask_le_last' ,[])]
targets1+= [
    ('mask_gt_first',[
        ('mask_ge_first',lambda sig:Binary(0,width=1)*sig.mask_ge_first[:-1])]),
    ('mask_lt_first',[
        ('mask_ge_first',lambda sig:~sig.mask_ge_first),
        ('mask_gt_first',lambda sig:~sig.mask_gt_first[1:]*~sig.exist.lvs[-1])]),
    ('mask_le_first',[
        ('mask_lt_first',lambda sig:Binary(1,width=1)*sig.mask_lt_first[:-1]),
        ('mask_gt_first',lambda sig:~sig.mask_gt_first),
        ('mask_ge_first',lambda sig:Binary(1,width=1)*~sig.mask_gt_first[:-1])])]
targets1+= [
    ('mask_lt_last',[
        ('mask_le_last',lambda sig:Binary(0,width=1)*sig.mask_le_last[:-1])]),
    ('mask_gt_last',[
        ('mask_le_last',lambda sig:~sig.mask_le_last),
        ('mask_gt_last',lambda sig:~sig.mask_lt_last[1:]*~sig.exist.lvs[-1])]),
    ('mask_ge_last',[
        ('mask_gt_last',lambda sig:Binary(1,width=1)*sig.mask_gt_last[:-1]),
        ('mask_lt_last',lambda sig:~sig.mask_lt_last),
        ('mask_le_last',lambda sig:Binary(1,width=1)*~sig.mask_lt_last[:-1])])]
targets2 = ['sel_first','sel_last']
makes1 = dict((target,d['make_'+target]) for target,reuse in targets1)
makes2 = dict((target,d['make_'+target]) for target in targets2)
def make(sig,io=None,enable_reuse=True,**kwargs):
    if not hasattr(sig,'exist'):
        sig.exist = make_exist(sig,io=io if kwargs.get('exist',False) else None)
    for target,reuse in targets1:
        if target not in kwargs:continue
        val = kwargs[target]
        del kwargs[target]
        if not val:continue
        if hasattr(sig,target):continue
        if enable_reuse:
            for pre,func in reuse:
                if hasattr(sig,pre):
                    setattr(sig,target,Wire(func(sig)))
                    break
        if hasattr(sig,target):continue
        setattr(sig,target,makes1[target](sig.exist,io=io))
    for target in targets2:
        if target not in kwargs:continue
        val = kwargs[target]
        del kwargs[target]
        if val is None:continue
        if hasattr(sig,target):continue
        setattr(sig,target,makes2[target](sig.exist,val,io=io))
    if len(kwargs)==0:return
    print('Targets are not implemented:')
    for target in kwargs:
        print(target)
    raise NotImplementedError(kwargs)
    
def _add1(a,b,c=None):return (a&b,a^b) if c is None else (a&b|b&c|a&c,a^b^c)
def count_one8(sig,io=None):
    num = Wire(clog2(len(sig)),io=io)
    num.c = Wire(3)
    num.s = Wire(3)
    for i in [0,1,2]:
        c,s = _add1(sig[i*3],sig[i*3+1],sig[i*3+2] if i*3+2<8 else None)
        num.c[i] = c
        num.s[i] = s
    num.c.c,num.c.s = _add1(num.c[0],num.c[1],num.c[2])
    num.s.c,num.s.s = _add1(num.s[0],num.s[1],num.s[2])
    num[0] = num.s.s
    num[1] = num.c.s^num.s.c
    num[2] = num.c.c^(num.c.s&num.s.c)
    return num
def _count_ok(lv,count=2):
    for i in range(len(lv.idxs)):
        if len(lv.idxs[i].sigs)>count:return False
    return True
def count_one(sig,io=None):
    if len(sig)==8:return count_one8(sig,io=io)
    raise NotImplementedError()
    num = Wire(clog2(len(sig)),io=io)
    num.enable_ssa('lv')
    lv = VStruct()
    num.lv = lv
    lv.idx  = VStruct()
    lv.idxs = [lv.idx]
    lv.idx.sigs =  sig
    while not _count_ok(num.lv,2):
        lv = VStruct()
        raise NotImplementedError()
    if not _count_ok(num.lv,1):
        pass
    for i in range(len(num)):
        num[i] = num.lv.idxs[i].sig
    return num