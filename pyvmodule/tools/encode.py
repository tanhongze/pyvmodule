from pyvmodule import *
from .gray_code import GrayCode
class Encoder:
    def __init__(self,width,exist=False,more=False,priority='none'):
        self.exist = exist
        self.more = more
        self.width = width
        self.log_width = clog2(self.width)
        self.priority = priority
    def implement(self):
        class encoder(VModule):
            if priority=='none':
                name = 'encoder_%d'%(self.width)
            else:
                name = 'encoder_%d_%s_prior'%(self.width,self.priority)
            if self.exist:
                name+='_exist'
            if self.more:
                name+='_more'
            data_in = Wire(self.width,io='input')
            data_out = Wire(self.log_width,io='output')
            exists = self.build_exist(data_in)
            if self.exist:
                exists[-1][0].name = 'exist'
                exists[-1][0].io='output'
            regist(exists)
            if self.more:
                mores = self.build_more(data_in,exists)
                mores[-1][0].name = 'more'
                mores[-1][0].io='output'
                regist(mores)
            exprs = self.build_encode(data_in,exists)
            for i in range(len(data_out)):
                data_out[i] = exprs[i]
            def encode(self,data,code=None):
                self.data_in = data
                self.data_out = Wire(len(self.data_out)) if code==None else code
                return self.data_out
        return encoder
    @classmethod
    def build_exist(cls,data,prefix=''):
        width = len(data)
        assert width>0
        if width<=1:
            return [[Wire(data[0])]]
        exists = [[data[i] for i in range(width)]]
        lv = 0
        if prefix != '' and prefix[-1]!='_':
            prefix+= '_'
        while len(exists[-1])>1:
            exists.append([])
            for i in range(0,len(exists[-2])-1,2):
                base = i<<lv
                stop = min(width,(i+2)<<lv)
                exists[-1].append(Wire(exists[-2][i]|exists[-2][i+1],name='%sexist_%d_%d'%(prefix,base,stop)))
            if len(exists[-2])&1:
                exists[-1].append(exists[-2][-1])
            lv += 1
        exists.pop(0)
        return exists
    @classmethod
    def build_more(cls,data,exists,prefix=''):
        width = len(data)
        if prefix != '' and prefix[-1]!='_':
            prefix+= '_'
        assert width>0
        if width<=1:
            return [[Wire(Binary(0,width=1))]]
        exists = [[valid[i] for i in range(len(valid))]] + exists
        mores = [[Binary(0,width=1) for i in range(width)]]
        lv = 0
        while len(mores[-1])>1:
            mores.append([])
            for i in range(0,len(mores[-2])-1,2):
                base = i<<lv
                stop = min(width,(i+2)<<lv)
                mores[lv+1].append(Wire(mores[lv][i]|mores[lv][i+1]|exists[lv][i]&exists[lv][i+1],name='%smore_%d_%d'%(prefix,base,stop)))
            if len(mores[lv])&1:
                mores[lv+1].append(mores[lv][-1])
            lv += 1
        mores.pop(0)
        return mores
    @classmethod
    def build_encode(cls,data,exists,priority='none',prefix=''):
        assert priority in {'none','high','low'}
        if prefix != '' and prefix[-1]!='_':
            prefix+= '_'
        # use build_exist to build exists 
        width = len(data)
        if width<=1:
            assert width>0
            return [[Wire(expr=Binary(0,width=1),name='subcode_0_%d'%width)]]
        exists = [[valid[i] for i in range(len(valid))]] + exists
        subcodes = [[0 for i in range(width)]]
        lv = 0
        while len(subcodes[-1])>1:
            subcodes.append([])
            for i in range(0,len(subcodes[-2])-1,2):
                stop = min(len(valid),(i+2)<<lv)
                exist_lo = exists[lv][i]
                exist_hi = exists[lv][i+1]
                if priority == 'high':
                    exist_lo&=~exist_hi
                elif priority == 'low':
                    exist_hi&=~exist_lo
                name = '%ssubcode_%d_%d'%(prefix,i<<lv,stop)
                subcode = Wire(lv+1,name=name)
                if lv>0:
                    expr = cond_if(exist_lo,subcodes[lv][i])
                    expr|= cond_if(exist_hi,subcodes[lv][i+1])
                    subcode[:-1] = expr
                subcode[-1] = exist_hi
                subcodes[lv+1].append(subcode)
            if len(subcodes[lv])&1:
                subcodes[lv+1].append(subcodes[lv][-1])
            lv += 1
        subcodes.pop(0)
        return subcodes
    @classmethod
    def build_select(cls,valid,exists,entries,priority='none',prefix=''):
        assert priority in {'none','high','low'}
        if prefix != '' and prefix[-1]!='_':
            prefix+= '_'
        # use build_exist to build exists 
        width = len(valid)
        if width<=1:
            assert width>0
            return [[Wire(entries[0],name='select_0_%d'%width)]]
        exists = [[valid[i] for i in range(len(valid))]] + exists
        selects = [entries]
        lv = 0
        while len(selects[-1])>1:
            selects.append([])
            for i in range(0,len(selects[-2])-1,2):
                stop = min(len(valid),(i+2)<<lv)
                exist_lo = exists[lv][i]
                exist_hi = exists[lv][i+1]
                if priority == 'high':
                    if selects[-1]==2:
                        expr = cond_if(exist_lo&~exist_hi,selects[lv][i])
                        expr|= cond_if(exist_hi,selects[lv][i+1])
                    else:
                        expr = Mux(exist_hi,selects[lv][i+1],selects[lv][i])
                elif priority == 'low':
                    if selects[-1]==2:
                        expr = cond_if(exist_lo,selects[lv][i])
                        expr|= cond_if(exist_hi&~exist_lo,selects[lv][i+1])
                    else:
                        expr = Mux(exist_lo,selects[lv][i],selects[lv][i+1])
                elif priority == 'none':
                    expr = cond_if(exist_lo,selects[lv][i])
                    expr|= cond_if(exist_hi,selects[lv][i+1])
                name = '%sselect_%d_%d'%(prefix,i<<lv,stop)
                selects[lv+1].append(Wire(expr,name=name))
            if len(selects[lv])&1:
                selects[lv+1].append(selects[lv][-1])
            lv += 1
        selects.pop(0)
        return selects