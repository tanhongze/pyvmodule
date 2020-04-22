__all__ = ['prepare_auto_connect']
import warnings
from pyvmodule import viterator as viter
from pyvmodule.wire import Wire
def get_match_table(obj,pattern,io):
    if pattern.count('*')>1:raise ValueError('Too many "*" to match.')
    index = pattern.find('*')
    cls = type(obj)
    if index<0:
        if pattern not in cls.mydict:return {}
        val = cls.mydict[pattern]
        if not isinstance(val,Wire) or val.io==None:return {}
        if io!=None and val.io!=io:return {}
        return {'':pattern}
    else:
        table = {}
        lhs = pattern[:index]
        rhs = pattern[index+1:]
        length = len(lhs)+len(rhs)
        for val in viter.ports(cls):
            val_name = val.name
            if val_name in obj.__dict__:continue
            if len(val_name)<length:continue
            if lhs!=val_name[:len(lhs)]:continue
            if len(rhs)>0 and rhs!=val_name[-len(rhs):]:continue
            if not io is None and val.io!=io:continue
            core = val_name[len(lhs):len(val_name)-len(rhs)]
            table[core] = val_name
        return table
def gen_name(pattern,core,name):
    result = pattern
    result = result.replace('*',core)
    result = result.replace('+',name)
    return result
port_dual = {'input':'output','output':'input','inout':'inout'}
def prepare_auto_connect_funcs(hasval,getval,setval):
    def auto_connect_ms(env,m,s,name,io):
        assert isinstance(s,str)
        assert m.typename == 'module'
        ttable = get_match_table(m,s,io)
        if len(ttable)==0:warnings.warn('No port matches "%s" in module "%s".'%(type(m).name))
        for tcore in ttable:
            k = ttable[tcore]
            p = gen_name(name,tcore,k)
            if hasval(env,p):
                pval = getval(env,p)
                if not isinstance(pval,Wire):raise TypeError('"%s" variable "%s" in parent is not a wire.'%(type(pval),p))
            else:
                port = getattr(m,k)
                pval = type(port)(width=len(port),name=p,io=io)
                setval(env,p,pval)
            setattr(m,k,pval)
    def auto_connect_mmss(env,m1,m2,s1,s2,name,io):
        assert m1.typename == 'module'
        assert m2.typename == 'module'
        t1 = get_match_table(m1,s1,io)
        t2 = get_match_table(m2,s2,io)
        for core in t1:
            if core not in t2:continue
            k1 = t1[core]
            k2 = t2[core]
            kp = gen_name(name,core,k1)
            port1 = m1.mydict[k1]
            port2 = m2.mydict[k2]
            if port_dual[port1.io]!=port2.io:
                raise TypeError('Unmatched input-output port type, from %s of "%s" to %s of "%s"'%(k1,port1.io,k2,port2.io))
            if hasval(env,kp):
                pval = getval(env,kp)
                if not isinstance(pval,Wire):raise TypeError('"%s" variable "%s" in parent is not a wire.'%(type(pval),kp))
            else:
                pval = sobj.mydict[skey].copy()
                pval.name = kp
                pval.io = io
                setval(env,kp,pval)
            setattr(sobj,skey,pval)
            setattr(tobj,tkey,pval)
    def auto_connect_m(env,m,name,io):
        auto_connect_ms(env,m,'*',name,io)
    def auto_connect_mx(env,m,x,name,io):
        if isinstance(x,str):auto_connect_ms(env,m,x,name,io)
        elif isinstance(x,list):
            for s in x:auto_connect_ms(env,m,s,name,io)
        else:auto_connect_mm(env,m,x,name,io)
    def auto_connect_mm(env,m1,m2,name,io):
        return auto_connect_mmss(env,m1,m2,'*','*',name,io)
    def auto_connect_mmx(env,m1,m2,x,name,io):
        if isinstance(x,list):
            for s in x:auto_connect_ms(env,m,s,name,io)
        else:return auto_connect_mmss(env,m1,m2,x,x,name,io)
    def auto_connect_mms(env,m1,m2,s,name,io):
        return auto_connect_mmss(env,m1,m2,s,s,name,io)
    return {1:auto_connect_m,2:auto_connect_mx,3:auto_connect_mms,4:auto_connect_mms}
hasitem = lambda self,key:key in self
getitem = lambda self,key:self[key]
def setitem(self,key,val):self[key] = val
meta_auto_connect_funcs = prepare_auto_connect_funcs(hasattr,getattr,setattr)
dict_auto_connect_funcs = prepare_auto_connect_funcs(hasitem,getitem,setitem)
def prepare_auto_connect(mydict,isdict):
    auto_connect_funcs = dict_auto_connect_funcs if isdict else meta_auto_connect_funcs
    def auto_connect(*args,name='+',io=None):
        if len(args)<=0:raise TypeError('Too few arguments for "auto_connect".')
        if len(args)> 4:raise TypeError('Too many arguments for "auto_connect".')
        if name.count('*')+name.count('+')>1:raise ValueError('Too many "*" or "+" in name pattern "%s".'%name)
        auto_connect_funcs[len(args)](mydict,*args,name,io)
    return auto_connect
