#coding=utf-8
import xlrd
import os
__all__ = ['Field','Entry','SheetParser','BitDoc']
class Field:
    _name_force_lower = True
    def raise_error(self,msg):
        raise ValueError('%s At %s.'%(msg,self.entry.location))
    @property
    def name(self):return self._name
    @name.setter
    def name(self,name):
        if name=='':self.raise_error('Empty name in "%s".'%self.entry.name)
        if not name[0].isidentifier():
            raise NameError('Name "%s" is invalid in "%s". At %s.'%(self.field,self.entry.name,self.entry.location))
        for i in range(1,len(name)):
            c = name[i]
            if not c.isalnum() and c !='_':
                self._name_origin = name[:i]
                break
        else:
            self._name_origin = name
        self._name = self._name_origin.lower().replace('.','_')
    def __init__(self,entry,start,end,width,mask,field,*args,**kwargs):
        self.entry = entry
        self.start = start
        self.end = end
        self.width = width
        self.mask = mask
        self.field = field
        self.name  = field
        self.parse(field[len(self.name):])
    def parse(self,*args,**kwargs):pass
def get_bin(t):
    s = t.replace(' ','').replace('\n','').replace('\t','')
    v = 0
    for c in s:
        v<<=1
        if c =='1':v|=1
        elif c!='0':raise ValueError(t)
    return v
class Entry:
    _name_force_lower = True
    @property
    def name(self):return self._name
    @name.setter
    def name(self,name):
        self._name_origin = name
        self._name = self._name_origin.replace(' ','').replace('.','_')
        if self._name_force_lower:self._name = self._name.lower()
    @property
    def impl(self):return self._impl
    @impl.setter
    def impl(self,impl):
        if impl == 'Y':self._impl = True
        elif impl == 'N':self._impl = False
        else:
            print(str(impl))
            raise ValueError(self.location)
    @property
    def sheet(self):return self._sheet
    @property
    def origin(self):return self._origin
    @property
    def doc(self):return self._sheet.doc
    @property
    def bit_width(self):return self.sheet.bit_width
    @property
    def location(self):return '<Location File="%s",Sheet="%s",Row="%s"/>'%self._location
    @classmethod
    def detect_keywords(cls):
        cls._kw_fields = {}
        for name in cls.__dict__:
            if name.startswith('parse_kw_'):
                name = name[len('parse_kw_'):]
                cls._kw_fields[name.lower()] = name
    def __init__(self,sheet,location,origin):
        self._impl = True
        self.bitfields = {}
        self._sheet = sheet
        self._location = location
        self._origin = origin
    def area_name(self,area_mask):
        name = None
        for field_name in self.fields:
            if area_mask==self.area_mask(field_name):
                if name is None:name = field_name
                else:raise RuntimeError('Duplicated field')
        return name
    def parse_kw(self,start,end,width,mask,field):
        name = field.lower()
        res  = self._kw_fields.get(name,None)
        if res is None:return False
        elif res==field:getattr(self,'parse_kw_'+res)(start,end,width,mask)
        else:raise NameError('Keyword should be "%s", not "%s". At %s.'%(res,field,self.location))
        return True
    def parse_field(self,*args,**kwargs):
        if not self.impl:return True
        if self.parse_kw(*args,**kwargs):return True
        f = self.Field(self,*args,**kwargs)
        if f.name in self.bitfields:
            raise NameError('Field "%s" is redefined in "%s". At %s.'%(f.name,self.name,self.location))
        self.bitfields[f.name] = f
        setattr(self,'field_'+f.name,f)
        return True
    def parse_field_end(self):pass
    def commit(self,doc):doc.entries.append(self)
    @staticmethod
    def bool_property(name,default=False):
        save = '_'+name
        def get(self):
            if hasattr(self,save):return getattr(self,save)
            else:return default
        def set(self,val):
            setattr(self,save,True if val == 'Y' else False)
        return property(get,set)
    @staticmethod
    def int_property(name,default=0):
        save = '_'+name
        def get(self):
            if hasattr(self,save):return getattr(self,save)
            else:return default
        def set(self,val):setattr(self,save,int(val) if val!='' else default)
        return property(get,set)
    @staticmethod
    def binary_property(name,default=0):
        save = '_'+name
        def get(self):
            if hasattr(self,save):return getattr(self,save)
            else:return default
        def set(self,val):setattr(self,save,get_bin(val) if val!='' else default)
        return property(get,set)
    @staticmethod
    def belonging_property(name):
        def get(self):return self.sheet.name == name
        return property(get)
    @staticmethod
    def encoded_property(name,encodes,default=0):
        save = '_'+name
        def get(self):
            if hasattr(self,save):return getattr(self,save)
            else:return default
        def set(self,val):
            setattr(self,save,encodes[val] if val!='' else default)
        return property(get,set)
    @staticmethod
    def named_property(name,default=''):
        save = '_'+name
        def get(self):
            if hasattr(self,save):return getattr(self,save)
            else:return default
        def set(self,val):
            if not isinstance(val,str):raise TypeError(type(val),val)
            setattr(self,save,val.lower())
        return property(get,set)
class SheetParser:
    @property
    def doc(self):return self._doc
    def __init__(self,doc,sheet,EntryParser,**kwargs):
        self._doc = doc
        self.sheet  = sheet
        self.EntryParser = EntryParser
        self.kwargs = kwargs
        
        self.name = sheet.name
        self.rename = kwargs.get('rename',{})
        
        self.locate_cols(sheet.row_values(0))
        self.map_merged_cells()
        self.parse(sheet)
    def bit_cols(self,loc):return self.bit_col_base + self.bit_col_dire*loc
    def bit_locs(self,col):return self.bit_col_dire*(col-self.bit_col_base)
    def locate_cols(self,title):
        bit_cols = {}
        bit_locs = {}
        self.titles = []
        self.name_cols = {}
        for col in range(len(title)):
            name = title[col]
            if isinstance(name,int):pass
            elif isinstance(name,float):name = int(name+0.5)
            if isinstance(name,str):
                name = name.replace(' ','').replace('\n','').replace('\t','')
                name = self.rename.get(name,name)
                if name.isnumeric():name=int(name)
            self.titles.append(name)
            if isinstance(name,str):
                if not name.isidentifier():raise NameError('Name "%s" is not an identifier.'%name)
                self.name_cols[name] = col
                setattr(self,'col_'+name,col)
            elif isinstance(name,int):
                loc = name
                if loc in bit_cols:
                    print('>>><<<')
                    print(loc)
                    print(bit_cols)
                    raise IndexError('Bit column "%s" is repeated.'%loc)
                if loc < 0:raise IndexError('Bit column "%s" should not be negative.'%loc)
                bit_locs[col] = loc
                bit_cols[loc] = col
            else:raise NameError('Unrecognized column title name "%s".'%name)
        if len(bit_cols)==0:
            self.bit_width = 0
            return
        # bit columns must be 0,1,...,bit_width-1
        self.bit_width = max(loc for loc in bit_cols)+1
        if len(bit_cols)<self.bit_width:
            for i in range(self.bit_width):
                if i not in bit_cols:
                    print('Bit column "%d" is missed.'%i)
            raise IndexError('Bit column missing.')
        self.bit_col_base = bit_cols[0]
        self.bit_col_dire = 1 if bit_cols[1]>self.bit_col_base else -1
        for loc,col in bit_cols.items():
            if self.bit_locs(col)!=loc:raise ValueError('Out Of Order.')
            if self.bit_cols(loc)!=col:raise ValueError('Out Of Order.')
    def _read_as_int(self,row,col):
        ctype = self.sheet.cell(row,col).ctype
        value = self.sheet.cell_value(row,col)
        if ctype == 0:# empty
            raise NotImplementedError('')
        if ctype == 1:# text
            return int(value)
        if ctype == 2:# value
            if value % 1 == 0.0:
                return int(value)
            else:
                raise NotImplementedError('')
        if ctype == 3:# date
            raise NotImplementedError('')
        if ctype == 4:# boolean
            raise NotImplementedError('')
        if ctype == 5:# error
            raise NotImplementedError('')
    def _read_as_str(self,row,col):
        ctype = self.sheet.cell(row,col).ctype
        value = self.sheet.cell_value(row,col)
        if ctype == 0:# empty
            return ''
        if ctype == 1:# text
            return str(value)
        if ctype == 2:# value
            if value % 1 == 0.0:
                return str(int(value))
            else:
                raise NotImplementedError('')
        if ctype == 3:# date
            raise NotImplementedError('')
        if ctype == 4:# boolean
            raise NotImplementedError('')
        if ctype == 5:# error
            raise NotImplementedError('')
    def map_merged_cells(self):
        self.merged_cell_map = {}
        self.merged_cell_val = {}
        for entry in self.sheet.merged_cells:
            row_start,row_stop,col_start,col_stop = entry
            for i in range(row_start,row_stop):
                for j in range(col_start,col_stop):
                    self.merged_cell_map[(i,j)] = entry
            self.merged_cell_val[entry] = self._read_as_str(row_start,col_start)
    def parse(self,sheet):
        self.entries = []
        for rowx in range(1,sheet.nrows):
            values = sheet.row_values(rowx)
            for col in range(len(values)):
                values[col] = self._read_as_str(rowx,col)
            docloc = (self.doc.filename,self.name,rowx+1)
            entry = self.EntryParser(self,docloc,values)
            for name,col in self.name_cols.items():
                setattr(entry,name,self._read_as_str(rowx,col))
            if not entry.impl:continue
            self.entries.append(entry)
            if self.bit_width <= 0:
                entry.parse_field_end()
                continue
            mask_done = 0
            for loc in range(self.bit_width):
                if (mask_done>>loc)&1:continue
                col = self.bit_cols(loc)
                pt = (rowx,col)
                if pt in self.merged_cell_map:
                    cell_loc = self.merged_cell_map[pt]
                    row_start,row_stop,col_start,col_stop = cell_loc
                    loc_start,loc_end = self.merged_cell_area(col_start,col_stop)
                    width = loc_end-loc_start
                    mask = ((1<<(width))-1)<<loc_start
                    val = self.merged_cell_val[cell_loc]
                else:
                    loc_start = loc
                    loc_end = loc+1
                    width = 1
                    mask = 1<<loc
                    val = self._read_as_str(rowx,col)
                val = val.strip()

                entry.parse_field(loc_start,loc_end,width,mask,val)
                mask_done |= mask
            entry.parse_field_end()
    def merged_cell_area(self,start,stop):
        if self.bit_col_dire<0:return (self.bit_locs(stop-1),self.bit_locs(start)+1)
        else:return (self.bit_locs(start),self.bit_locs(stop-1)+1)
    def commit(self):
        for entry in self.entries:
            entry.commit(self.doc)
def display(res,path=None,to_screen=True):
    if to_screen or path is None:print(res)
    if path is None:return
    path = os.path.abspath(path)
    print('Output to path:',path)
    with open('/path/to/file', 'r') as f:
        print(res,file=f)
class BitDoc:
    def __init__(self,filename,sheetnames,Parser,**kwargs):
        self.entries = []
        self.kwargs = kwargs
        self.filename = filename
        self.sheetnames = sheetnames
        self.workbook = xlrd.open_workbook(filename=filename)
        self.sheets = [SheetParser(self,self.workbook.sheet_by_name(sheetname),Parser,**kwargs) for sheetname in sheetnames]
        for sheet_parser in self.sheets:sheet_parser.commit()
        self.commit_end()
    def commit_end(self):pass
    def gen(self,name,lib='targets'):
        mname = '%s.%s'%(lib,name)
        gen = __import__(mname,fromlist=[name])
        return getattr(gen,'gen_%s'%name)(self)
    def make(self,odir='./gen/',lib='targets',**kwargs):
        for name,ofname in kwargs.items():
            display(self.gen(name,lib=lib),odir+ofname if not ofname is None else None)
        
