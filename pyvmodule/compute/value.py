from pyvmodule.ast import ASTNode
__all__ = ['expr_value_calc_funcs','expr_value_prop_funcs']
def calc_bitwise_xor(expr):
    x = int(expr.rhs)
    if x<0:raise ValueError('Bit reduction of infinite width value.')
    i = 1
    while i<=x:
        x = x^(x>>i)
        i<<=1
    return x&1
def calc_bitwise_and(expr):
    x = int(expr.rhs)
    n = len(expr.rhs)
    if x<0:return x==-1
    m = (1<<n)-1
    return x==m
def calc_replicate(expr):
    rhs = expr.rhs
    m = len(rhs)
    n = len(expr)
    v = int(rhs)
    while m<n:
        v |= v<<m
        m<<=1
    v &= (1<<n)-1
    return v
def calc_concatenate(expr):
    y = 0
    for i in range(len(expr.childs)-1,-1,-1):
        y<<=len(expr.childs[i])
        y |=int(expr.childs[i])
    return y
def calc_fetch(expr):
    typename = expr.rhs.typename
    if typename == 'range':
        if expr.lhs.length>1:return expr.lhs.value[expr.rhs.start]
        else:return (int(expr.lhs)>>expr.rhs.start)&((1<<expr.rhs.width)-1)
    elif typename == '+:':return (int(expr.lhs)>>int(expr.rhs.start))&((1<<expr.rhs.width)-1)
    elif typename == '-:':return((int(expr.lhs)<<expr.rhs.width)>>int(expr.rhs.stop))&((1<<expr.rhs.width)-1)
    else:assert False
def prop_value(expr):
    return expr._wrap_constant(int(expr))
def prop_default(expr):
    for child in expr.childs:
        if not child._is_constant:return expr
    return prop_value(expr)
def prop_shift(expr):
    if expr.rhs._is_constant:
        if int(expr.rhs)==0:return expr.lhs
        else:return expr
    else:return expr
def prop_xor_half(v,c,e):
    if c==0:return v
    elif c==(1<<len(e))-1:return ~v
    else:return e
def prop_and_half(v,c,e):
    if c==0:return e._wrap_constant(0)
    elif c==(1<<len(e))-1:return v
    else:return e
def prop_or_half(v,c,e):
    if c==0:return v
    elif c==(1<<len(e))-1:return e._wrap_constant(-1)
    else:return e
def prop_add_half(v,c,e):
    if c==0:return v
    elif len(e)==1:return prop_xor_half(v,c,e)
    else:return e
def prop_abelian(prop_func):
    def prop(expr):
        if expr.width is None:return prop_default(expr)
        elif expr.lhs._is_constant:
            if expr.rhs._is_constant:return prop_value(expr)
            else:return prop_func(expr.rhs,int(expr.lhs),expr)
        else:
            if expr.rhs._is_constant:return prop_func(expr.lhs,int(expr.rhs),expr)
            else:return expr
    return prop
prop_xor_lr = prop_abelian(prop_xor_half)
prop_and_lr = prop_abelian(prop_and_half)
prop_or_lr  = prop_abelian(prop_or_half )
prop_add_lr = prop_abelian(prop_add_half)
def prop_xor(expr):
    if len(expr.childs)>2:return expr
    if expr.lhs is expr.rhs:return expr._wrap_constant(0)
    else:return prop_xor_lr(expr)
def prop_and(expr):
    if len(expr.childs)>2:return expr
    if expr.lhs is expr.rhs:return expr.lhs
    else:return prop_and_lr(expr)
def prop_or(expr):
    if len(expr.childs)>2:return expr
    if expr.lhs is expr.rhs:return expr.lhs
    else:return prop_or_lr(expr)
def prop_add(expr):
    if len(expr.childs)>2:return expr
    if expr.lhs is expr.rhs:
        if expr.width==1:return expr._wrap_constant(0)
        elif expr.lhs.typename in {'wire','reg'}:return expr._hex_value(0,width=1)*expr.lhs[1:]
        else:return prop_add_lr(expr)
    else:return prop_add_lr(expr)
def prop_sub_l(v,c,e):
    if c==0:return -v
    elif len(e)==1:return ~v
    else:return e
def prop_sub_r(v,c,e):
    if c==0:return v
    elif len(e)==1:return ~v
    else:return v+e._wrap_constant(-c)
def prop_nonabelian(prop_l,prop_r):
    def prop(expr):
        if expr.width is None:return prop_default(expr)
        elif expr.lhs._is_constant:
            if expr.rhs._is_constant:return prop_value(expr)
            else:return prop_l(expr.rhs,int(expr.lhs),expr)
        else:
            if expr.rhs._is_constant:return prop_r(expr.lhs,int(expr.rhs),expr)
            else:return expr
    return prop
prop_sub_lr = prop_nonabelian(prop_sub_l,prop_sub_r)
def prop_sub(expr):
    if expr.lhs is expr.rhs:return expr._wrap_constant(0)
    else:return prop_sub_lr(expr)
_invert_ops = {'==':'!=','!=':'==','<=':'>','>=':'<','>':'<=','<':'>='}
def prop_not(expr):
    if expr.rhs._is_constant:return prop_value(expr)
    else:
        typename = expr.rhs._typename
        if typename in {'~','!'}:return expr.rhs.rhs
        elif typename in _invert_ops:return type(expr.rhs)(_invert_ops[typename],expr.rhs.lhs,expr.rhs.rhs)
        else:return expr
def prop_bitreduce(expr):
    if expr.rhs._is_constant:return prop_value(expr)
    elif len(expr.rhs)==1:return expr.rhs
    else:return expr
def prop_mux(expr):
    if expr.cond._is_constant:
        if int(expr.cond)==0:return expr.rhs
        else:return expr.lhs
    elif expr.lhs is expr.rhs:return expr.lhs
    elif expr.lhs._is_constant:
        if expr.rhs._is_constant:
            if int(expr.lhs)==int(expr.rhs):return expr.lhs
            elif expr.width is None:return expr
            elif (int(expr.lhs)^int(expr.rhs))==(1<<len(expr))-1:return (expr.cond**len(expr))^expr.rhs
            else:return expr
        else:
            if int(expr.lhs)==0:return expr.rhs.validif(~expr.cond)
            elif expr.width==1:return expr.cond|expr.rhs
            else:return expr
    elif expr.rhs._is_constant:
        if int(expr.rhs)==0:return expr.lhs.validif(expr.cond)
        elif expr.width==1:return (~expr.cond)|expr.lhs
        else:return expr
    else:return expr
def prop_validif(expr):
    if expr.lhs._is_constant:
        if int(expr.lhs)==0:return expr._wrap_constant(0)
        else:return expr.rhs
    elif expr.width==1:return expr.lhs&expr.rhs
    elif expr.rhs._is_constant:
        c = int(expr.rhs)
        if c==0:return expr._wrap_constant(0)
        elif expr.width is None:return expr
        elif c==(1<<len(expr))-1:return expr.lhs ** len(expr)
        else:return expr
    else:return expr
def prop_never(expr):return expr
expr_value_calc_funcs = {
    'const'  :lambda expr:expr.value,
    'wire'   :lambda expr:expr.value,
    'reg'    :lambda expr:expr.value,
    '[]'     :calc_fetch,
    '^'      :lambda expr:int(expr.lhs)^int(expr.rhs),
    '&'      :lambda expr:int(expr.lhs)&int(expr.rhs),
    '|'      :lambda expr:int(expr.lhs)|int(expr.rhs),
    '+'      :lambda expr:int(expr.lhs)+int(expr.rhs),
    '-'      :lambda expr:int(expr.lhs)-int(expr.rhs),
    '*'      :lambda expr:int(expr.lhs)*int(expr.rhs),
    '/'      :lambda expr:int(expr.lhs)//int(expr.rhs),
    '%'      :lambda expr:int(expr.lhs)%int(expr.rhs),
    '=='     :lambda expr:1 if int(expr.lhs)==int(expr.rhs) else 0,
    '!='     :lambda expr:1 if int(expr.lhs)!=int(expr.rhs) else 0,
    '<='     :lambda expr:1 if int(expr.lhs)<=int(expr.rhs) else 0,
    '<'      :lambda expr:1 if int(expr.lhs)< int(expr.rhs) else 0,
    '>='     :lambda expr:1 if int(expr.lhs)>=int(expr.rhs) else 0,
    '>'      :lambda expr:1 if int(expr.lhs)> int(expr.rhs) else 0,
    '<<'     :lambda expr:int(expr.lhs)<<int(expr.rhs),
    '>>'     :lambda expr:int(expr.lhs)>>int(expr.rhs),
    '~'      :lambda expr:~int(expr.rhs),
    ' -'     :lambda expr:-int(expr.rhs),
    ' |'     :lambda expr:1 if int(expr.rhs)!=0 else 0,
    ' &'     :calc_bitwise_and,
    ' ^'     :calc_bitwise_xor,
    '?:'     :lambda expr:int(expr.lhs) if int(expr.cond)!=0 else int(expr.rhs),
    'validif':lambda expr:int(expr.lhs) if int(expr.rhs) !=0 else 0,
    '{}'     :calc_concatenate,
    '{{}}'   :calc_replicate}
expr_value_prop_funcs = {
    'const'  :prop_never,
    'wire'   :prop_never,
    'reg'    :prop_never,
    '^'      :prop_xor,
    '&'      :prop_and,
    '|'      :prop_or,
    '+'      :prop_add,
    '-'      :prop_sub,
    '*'      :prop_default,
    '/'      :prop_default,
    '%'      :prop_default,
    '=='     :prop_default,
    '!='     :prop_default,
    '<='     :prop_default,
    '<'      :prop_default,
    '>='     :prop_default,
    '>'      :prop_default,
    '<<'     :prop_shift,
    '>>'     :prop_shift,
    '~'      :prop_not,
    ' -'     :prop_default,
    ' |'     :prop_bitreduce,
    ' &'     :prop_bitreduce,
    ' ^'     :prop_bitreduce,
    '?:'     :prop_mux,
    'validif':prop_validif,
    '[]'     :prop_never,
    '{}'     :prop_default,
    '{{}}'   :prop_default}
