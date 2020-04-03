__all__ = ['meta_copy','module_copy','wire_copy','reg_copy']
from pyvmodule.naming import NamingRoot
def redecl_to_dict(mydict,base):
    for name,val in base._naming_var.items():
        if not val._naming_parent is base:continue
        mydict[name] = val._node_clone()
def redecl_to_parent(next,prev):
    for name,val in prev._naming_var.items():
        if not val._naming_parent is prev:continue
        setattr(next,name,val._node_clone())
def meta_copy(mydict,bases):
    for base in bases:
        if not isinstance(base,NamingRoot):continue
        redecl_to_dict(mydict,base)
            