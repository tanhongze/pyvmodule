from vmodule import Wire
def get_smart(name,default_val,kwargs):
    if name in kwargs:
        return kwargs[name]
    else:
        return default_val
def get_smart_func(name,default_func,kwargs):
    if name in kwargs:
        return kwargs[name]
    else:
        return default_func()
def get_clock(kwargs):
    return get_smart_func('clock',lambda:Wire(name='clock',io='input'),kwargs)
def get_reset(kwargs):
    return get_smart_func('reset',lambda:Wire(name='reset',io='input'),kwargs)