#coding=utf-8
from pyvmodule.develope import Wire,VStruct,decode
from .bitdoc import BitDoc,Entry,Field
from functools import reduce
__all__ = ['InstDoc']
class InstEntry(Entry):
    def __init__(self,*args,**kwargs):
        self.Field = Field
        self.mask = 0
        self.code = 0
        Entry.__init__(self,*args,**kwargs)
    def parse_kw_1(self,start,end,width,mask):
        assert width == 1
        self.mask |= mask
        self.code |= mask
    def parse_kw_0(self,start,end,width,mask):
        assert width == 1
        self.mask |= mask
def get_mask(r,l):
    return ((1<<(r-l))-1)<<l
def need_decode(mask,decoded,i):
    return 1 if ((mask>>i)&1)!=0 and ((decoded>>i)&1)==0 else 0
def decode_raw_remove_unused(doc,seg,l,r):
    mask = get_mask(r,l)
    using = set()
    for entry in doc.entries:
        if (mask & entry.mask) == mask:using.add(entry.code&mask)
    seg.dec = {}
    using = sorted([code>>l for code in using])
    for code in using:
        decx = Wire(seg.equal_to(code))
        setattr(seg,'dec%d'%code,decx)
        seg.dec[code] = decx
def decode_raw_keep_unused(doc,seg,l,r):
    seg.dec = decode(seg)
def decode_raw(doc,inst,l,r,subdec,remove_unused=True):
    seg = Wire(inst[l:r])
    (decode_raw_remove_unused if remove_unused else decode_raw_keep_unused)(doc,seg,l,r)
    subdec[get_mask(r,l)]=(l,r,seg.dec)
    return seg
def decode_buf_remove_unused(doc,seg,l,r,u,v,subdec,pivots):
    mask = get_mask(r,l)
    using = set()
    for entry in doc.entries:
        if (mask & entry.mask) == mask:using.add(entry.code&mask)
    using = set(code>>l for code in using)
    dec1 = {0:1}
    for x in range(u,v):
        next = {}
        dec2 = subdec[get_mask(pivots[x+1],pivots[x])][2]
        shift = pivots[x] - l
        for code2 in dec2:
            for code1 in dec1:
                next[(code2<<shift)|code1] = dec1[code1] & dec2[code2]
        dec1 = next
    dec = dec1
    for code in dec:
        if code not in using:continue
        decx = Wire(dec[code])
        setattr(seg,'dec%d'%code,decx)
        dec[code] = decx
    seg.dec = dec
def subcode(subdec,pivots,code,x):
    mask = get_mask(pivots[x+1],pivots[x])
    code = (code&mask)>>pivots[x]
    return subdec[mask][2][code]
def decode_buf_keep_unused(doc,seg,l,r,u,v,subdec,pivots):
    dec = Wire(1<<(r-l))
    for p in range(len(dec)):
        dec[p] = reduce(lambda x,y:x&y,(subcode(subdec,pivots,p<<l,x) for x in range(u,v)),1)
    seg.dec = dec
def decode_buf(doc,inst,l,r,subdec,u,v,pivots,remove_unused=True):
    seg = VStruct()
    (decode_buf_remove_unused if remove_unused else decode_buf_keep_unused)(doc,seg,l,r,u,v,subdec,pivots)
    subdec[get_mask(r,l)] = (l,r,seg.dec)
    return seg
def get_block(mask,decoded,i,boundary):
    for j in range(i+1,32):
        if boundary == need_decode(mask,decoded,j):return j
    return 32
class InstDoc(BitDoc):
    def __init__(self,filename,sheetnames,**kwargs):
        BitDoc.__init__(self,filename,sheetnames,InstEntry,**kwargs)
    def decode_rtl(self,inst,op,pivots=None,corners=None,prepares=None,judgers=None,subset=None,remove_unused=True):
        subdec = {}
        inst.segs = []
        if not corners is None:
            inst.enable_ssa('corseg')
            for l,r in corners:
                inst.corseg = decode_raw(self,inst,l,r,subdec,remove_unused=remove_unused)
                inst.segs.append('decode inst[%d:%d] -> %s'%(r-1,l,str(inst.corseg)))
        if not pivots is None:
            w = len(inst)
            for i in range(1,len(pivots)):
                if pivots[i][-1] != pivots[0][-1]:pivots[i].append(pivots[0][-1])
                if pivots[i][ 0] != pivots[0][ 0]:pivots[i].insert(0,pivots[0][ 0])
            inst.enable_ssa('lv')
            inst.lv = VStruct()
            inst.lv.enable_ssa('seg')
            for i in range(len(pivots[0])-1):
                l = pivots[0][i]
                r = pivots[0][i+1]
                inst.lv.seg = decode_raw(self,inst,l,r,subdec,remove_unused=remove_unused)
                inst.segs.append('decode inst[%d:%d] -> %s'%(r-1,l,str(inst.lv.seg)))
            for i in range(1,len(pivots)):
                inst.lv = VStruct()
                inst.lv.enable_ssa('seg')
                u = 0
                for j in range(len(pivots[i])-1):
                    l = pivots[i][j]
                    r = pivots[i][j+1]
                    v = pivots[i-1].index(pivots[i][j+1])
                    inst.lv.seg = decode_buf(self,inst,l,r,subdec,u,v,pivots[i-1],remove_unused=remove_unused)
                    inst.segs.append('decode inst[%d:%d] -> %s'%(r-1,l,str(inst.lv.seg)))
                    u = v
        if not prepares is None:
            for name,expr in prepares.items():
                setattr(inst,name,Wire(expr(inst))) 
        masks = sorted([mask for mask in subdec],reverse=True)
        for entry in self.entries:
            if not subset is None and not subset(entry):continue
            expr = 1
            decoded = 0
            for mask in masks:
                if (mask&entry.mask)!=mask or (mask&decoded)!=0:continue
                l,r,dec = subdec[mask]
                expr&= dec[(entry.code&mask)>>l]
                decoded|=mask
            i = get_block(entry.mask,decoded,-1,1)
            while i < 32:
                j = get_block(entry.mask,decoded,i,0)
                expr&= inst[i:j]//((entry.code&get_mask(j,i))>>i)
                i = get_block(entry.mask,decoded,j,1)
            if not judgers is None:
                if entry.judge!='':expr &= judgers[entry.judge](inst)
            setattr(op,entry.name,Wire(expr))