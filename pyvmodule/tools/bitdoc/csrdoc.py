#coding=utf-8
from pyvmodule.develope import VStruct,Wire,Reg,ctrlblk
from .bitdoc import BitDoc,Entry,Field
__all__ = ['CsrDoc','CsrEntry','CsrField']
class CsrField(Field):
    default_value = None
    rw_allowed = {'r','rr','rc','rw'}
    @property
    def rw(self):return self._rw
    @rw.setter
    def rw(self,rw):
        rw = rw.lower()
        if rw not in self.rw_allowed:
            self.raise_error('Invilad RW property "%s".'%rw)
        self._rw = rw
    def __init__(self,*args,**kwargs):
        self.rw   = 'rw'
        self.value= self.default_value
        self.export = False
        Field.__init__(self,*args,**kwargs)
    def parse(self,tail):
        parts = tail.split('$')
        for part in parts[1:]:
            pragma = part.strip()
            if pragma=='export':
                self.export = True
        text = parts[0]
        parts = text.split('=')
        if len(parts)> 2:raise ValueError(tail)
        if len(parts)<=1:
            parts = text.split(':')
            if len(parts)> 2:raise ValueError(tail)
            if len(parts)<=1:return
            self.rw = 'RC'
            exec('self.value = '+parts[1])
            return
        # <rw>:<val>
        text = parts[1]
        parts = text.split(':')
        if len(parts)> 2:raise ValueError(tail)
        self.rw = parts[0].strip()
        if len(parts)<=1:return
        exec('self.value = '+parts[1])
class CsrEntry(Entry):
    export = Entry.bool_property('export')
    id     = Entry.int_property('id')
    def parse_kw_Extend(self,start,end,width,mask):
        if len(self.area_extend)>0:raise ValuError('Multiple "Extend" area.')
        self.mask_extend  |=mask
        self.area_extend.append((start,end,width))
    def parse_kw_Ignore(self,start,end,width,mask):
        self.mask_ignore  |=mask
        self.area_ignore.append((start,end,width))
    def parse_kw_Reserved(self,start,end,width,mask):
        self.mask_reserved|=mask
        self.area_reserved.append((start,end,width))
    def __init__(self,*args,**kwargs):
        self.mask_reserved = 0
        self.area_reserved = []
        self.mask_ignore = 0
        self.area_ignore = []
        self.mask_extend = 0
        self.area_extend = []
        self.Field = CsrField
        Entry.__init__(self,*args,**kwargs)
CsrEntry.detect_keywords()
class CsrDoc(BitDoc):
    def __init__(self,filename,sheetnames,Entry=CsrEntry,**kwargs):
        BitDoc.__init__(self,filename,sheetnames,Entry,**kwargs)
    def csr_cls(self):
        class CSR(VStruct):
            entries = self.entries
            def read_with(self,raddr,io=None):
                rdata = Wire(self.entries[0].bit_width,io=io)
                rdata.hit = VStruct()
                r = 0
                for entry in self.entries:
                    hitcsr = Wire(raddr.equal_to(entry.id))
                    setattr(rdata.hit,entry.name,hitcsr)
                    r|=getattr(self,entry.name).validif(hitcsr)
                rdata[:] = r
                return rdata
            def write_with(self,reset,we,waddr,wdata,*args,**kwargs):
                self.reset = reset
                for entry in self.entries:
                    csr = getattr(self,entry.name)
                    if not hasattr(entry,'readonly') or not entry.readonly:
                        mywe = we&waddr.equal_to(entry.id)
                        if hasattr(entry,'lock'):
                            if isinstance(entry.lock,str):
                                if entry.lock!='':mywe&=getattr(self.lock,entry.lock)
                            elif isinstance(entry.lock,bool):
                                if entry.lock:mywe&=self.lock
                            else:raise TypeError(entry.lock)
                        csr.write = Wire(mywe)
                    csr.wdata = wdata
                for entry in self.entries:
                    csr = getattr(self,entry.name)
                    for name,field in entry.bitfields.items():
                        f = getattr(csr,name)
                        if field.rw == 'rc':
                            continue
                        custom_method = 'write_csr_%s_%s'%(entry.name,name)
                        if field.rw == 'rr':
                            getattr(self,custom_method)(f,wdata[field.start:field.end],*args,**kwargs)
                            continue
                        blk = ctrlblk
                        if not field.value is None:
                            blk = blk.When(reset)[f:field.value]
                        if field.rw == 'rw':
                            blk = blk.When(csr.write)[f:wdata[field.start:field.end]]
                        f.blk = blk
                        if hasattr(self,custom_method):
                            getattr(self,custom_method)(f,wdata[field.start:field.end],*args,**kwargs)
            def init_lock(self):pass
            def __init__(self,**kwargs):
                VStruct.__init__(self,**kwargs)
                for entry in self.entries:
                    csr = Wire(entry.bit_width,io='output' if entry.export else None)
                    setattr(self,entry.name,csr)
                    for start,end,width in entry.area_reserved:
                        csr[start:end] = 0
                    for start,end,width in entry.area_ignore:
                        csr[start:end] = 0
                    
                    extend_start = 0                    
                    if entry.mask_extend:
                        start,end,width = entry.area_extend[0]
                        if (entry.mask_extend>>1)&(entry.mask_reserved|entry.mask_ignore):
                            csr[start:end] = 0
                        if start==0:csr[start:end] = 0
                        extend_start = start
                    for name,field in entry.bitfields.items():
                        if field.rw=='r':
                            f = Reg (field.width,io='output' if field.export else None)
                        elif field.rw=='rr':
                            f = Wire(field.width,io='output' if field.export else None)
                        elif field.rw=='rc':
                            f = Wire(field.width,io='output' if field.export else None)
                            if field.value is None:raise ValueError('Marked as constant but not valued.')
                            else:f[:] = field.value
                        elif field.rw=='rw':
                            f = Reg(field.width)
                        f.field = field
                        setattr(csr,name,f)
                        csr[field.start:field.end] = f
                        f.csr = csr
                        if field.end == extend_start:csr[extend_start:] = f[-1]**(entry.bit_width-extend_start)
                self.lock = self.init_lock()
        return CSR
