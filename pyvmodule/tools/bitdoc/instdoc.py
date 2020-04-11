#coding=utf-8
from pyvmodule.develope import Wire,VStruct,decode,clog2,Hexadecimal
from .bitdoc import BitDoc,Entry,Field
from functools import reduce
__all__ = ['InstDoc','InstEntry','InstField']
class InstField(Field):
    @property
    def super_name(self):return self._name if self._super_name is None else self._super_name
    @property
    def super_start(self):return 0 if self.super_place is None else self.super_place[0]
    @property
    def super_end(self):return self.width if self.super_place is None else self.super_place[1]
    @property
    def super_width(self):return self.super_end - self.super_start
    @property
    def super_mask(self):return ((1<<self.super_width)-1)<<self.super_start
    def parse(self,tail):
        self.super_place = None
        self._super_name = None
        if tail.startswith('['):
            tail = tail[1:]
            area,tail = tail.split(']')
            area = area.split(':')
            if len(area)==1:self.super_place = (int(area[0]),int(area[0])+1)
            else:self.super_place = (int(area[1]),int(area[0])+1)
            self._super_name = self._name
            self._name = self._name + str(self.super_end)
class InstEntry(Entry):
    def __init__(self,*args,Field=InstField,**kwargs):
        self.Field = Field
        self.mask = 0
        self.code = 0
        self.superfields = {}
        Entry.__init__(self,*args,**kwargs)
    def parse_kw_1(self,start,end,width,mask):
        assert width == 1
        self.mask |= mask
        self.code |= mask
    def parse_kw_0(self,start,end,width,mask):
        assert width == 1
        self.mask |= mask
InstEntry.detect_keywords()
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
    def __init__(self,filename,sheetnames,Entry=InstEntry,**kwargs):
        BitDoc.__init__(self,filename,sheetnames,Entry,**kwargs)
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
    def summary_cls(self,names,selected=lambda entry:True):
        summary_infos = []
        def summary_bool_property(target,op,name):
            target[:] = reduce(lambda a,b:a|b,[getattr(op,entry.name) for entry in self.entries if selected(entry) and getattr(entry,name)],0)
        def summary_encoded_property(target,op,name):
            target[:] = reduce(lambda a,b:a|b,[Hexadecimal(getattr(entry,name),width=len(target)).validif(getattr(op,entry.name)) for entry in self.entries if selected(entry) and getattr(entry,name)],0)
        def summary_named_property(target,op,name):
            vals = {key:0 for key in target.mynames}
            for entry in self.entries:
                if not selected(entry):continue
                code = getattr(entry,name)
                if code == '':continue
                vals[code]|=getattr(op,entry.name)
            for name,val in vals.items():
                getattr(target,name)[:] = val
        for name in names:
            val = getattr(self.entries[0],name)
            if isinstance(val,bool):# deal with Y / N properties
                summary_infos.append((name,1,Wire,summary_bool_property))
            elif isinstance(val,int):# 0,1,2,3
                width = clog2(max(getattr(entry,name) for entry in self.entries)+1)
                if width==0:raise ValueError('Invalid encoding field "%s"'%name)
                summary_infos.append((name,width,Wire,summary_encoded_property))
            elif isinstance(val,str):# a,b,c,d
                val_set = set(getattr(entry,name) for entry in self.entries)
                val_set.remove('')
                class OnehotNames(VStruct):
                    mynames = val_set
                    def __init__(self,width=None,io=None,**kwargs):
                        VStruct.__init__(self,**kwargs)
                        for myname in self.mynames:
                            setattr(self,myname,Wire(width=1,io=io))
                summary_infos.append((name,1,OnehotNames,summary_named_property))
            else:
                raise TypeError()
        class InfoSummary(VStruct):
            infos = summary_infos
            def __init__(self,io=None,**kwargs):
                VStruct.__init__(self,**kwargs)
                for myname,width,T,method in self.infos:
                    setattr(self,myname,T(width=width,io=io))
            def assigned_with(self,op):
                for myname,width,T,method in self.infos:
                    method(getattr(self,myname),op,myname)
        return InfoSummary
