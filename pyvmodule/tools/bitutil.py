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
    enc[:] = enc.lvs[-1].code
    return enc

def make_last  (exist,**kwargs):return _make_fst_lst(exist,_last_sel ,_last_enc ,**kwargs)
def make_first (exist,**kwargs):return _make_fst_lst(exist,_first_sel,_first_enc,**kwargs)

def make_onehot(exist,io=None):
    if exist is None:exist = sig.exist
    enc = Wire(clog2(len(exist.lvs[0])),io=io)
    for i in range(len(enc)):
        expr = 0
        elv = exist.lvs[i]
        for j in range(1,len(elv),2):
            expr|= elv[j]
        enc[i] = expr
    return enc
d = vars()
targets = ['exist','first','last','onehot']#\
    #+['mask_first','mask_le_first','mask_ge_first','mask_lt_first','mask_gt_first']#\
    #+['mask_last' ,'mask_le_last' ,'mask_ge_last' ,'mask_lt_last' ,'mask_gt_last' ]
makes = dict((target,d['make_'+target]) for target in targets)
def make(sig,io=None,**kwargs):
    for target in targets:
        if kwargs.get(target,False):
            sig.exist = make_exist(sig,io=io if kwargs.get('exist',False) else None)
            break
    for i in range(1,len(targets)):
        target = targets[i]
        if hasattr(sig,target):continue
        if kwargs.get(target,False):setattr(sig,target,makes[target](sig.exist,io=io))
    return