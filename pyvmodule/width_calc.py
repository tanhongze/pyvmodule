from .exceptions import a_width_positive,a_width_match
__all__ = ['expr_match_width','expr_calc_width','expr_width_fix_funcs','expr_width_calc_funcs']
def get_width(src):return src if src is None or isinstance(src,int) else src.width 
def expr_match_width(source,expect=None):
    source_width = get_width(source)
    expect_width = get_width(expect)
    if expect_width is None: # not constrained
        if source_width is None:raise ValueError('Width of "%s" is undetermined .'%str(source))
        else:return False
    elif source_width is None: # fix the width with the expected width
        a_width_positive(expect_width,expect)
        source.width = expect_width 
        return True
    else:
        a_width_positive(expect_width,expect)
        a_width_positive(source_width,source)
        a_width_match   (source_width,source,expect_width,expect)
        return False
def expr_calc_width(lhs,rhs):
    if not lhs.width is None:
        if rhs.width is None:rhs._fix_width(lhs)
        else:expr_match_width(lhs,rhs)
    elif not rhs.width is None:lhs._fix_width(rhs)
def fix_width_x(expr,expected): expr_match_width(expr,expected)
def fix_width_x_x(expr,expected):
    if expr_match_width(expr,expected):
        expr.rhs._fix_width(expected)
def fix_width_1_x(expr,expected):expr_match_width(expr,expected)
def fix_width_x_xx(expr,expected):
    if expr_match_width(expr,expected):
        expr.lhs._fix_width(expected)
        expr.rhs._fix_width(expected)
def fix_width_x_xy(expr,expected):
    if expr_match_width(expr,expected):
        expr.lhs._fix_width(expected)     
def fix_width_x_yx(expr,expected):
    if expr_match_width(expr,expected):
        expr.rhs._fix_width(expected)
def fix_width_1_xx(expr,expected):expr_match_width(expr,expected)
def fix_width_x_xi(expr,expected):
    if expr_match_width(expr,expected):
        for child in expr.childs:
            child._fix_width(expected)
def fix_width_s_xi(expr,expected):expr_match_width(expr,expected)
def fix_width_p_xn(expr,expected):expr_match_width(expr,expected)
def fix_width_fetch(expr,expected):expr_match_width(expr,expected)
def calc_width_(expr):raise NotImplementedError()
def calc_width_x_x(expr):
    expr.width = expr.rhs.width
def calc_width_1_x(expr):
    expr_match_width(expr.rhs)
    expr.width = 1
def calc_width_x_xx(expr):
    expr_calc_width(expr.lhs,expr.rhs)
    expr.width = expr.lhs.width
def calc_width_x_xy(expr):
    expr.width = expr.lhs.width
    expr_match_width(expr.rhs)
def calc_width_x_yx(expr):
    expr.width = expr.rhs.width
    expr_match_width(expr.lhs)
def calc_width_1_xx(expr):
    expr_calc_width(expr.lhs,expr.rhs)
    if expr.lhs.width is None and expr.rhs.width is None:
        if expr.rhs.width is None:expr_match_width(expr.lhs,expr.rhs)
        else:expr.lhs._fix_width(expr.rhs)
    else:
        if expr.rhs.width is None:expr.rhs._fix_width(expr.lhs)
        else:expr_match_width(expr.lhs,expr.rhs)
    expr.width = 1
def calc_width_x_xi(expr):
    id = None
    child = None
    childs = expr.childs
    for i in range(len(childs)):
        if not childs[i].width is None:
            id = i
            child = childs[i]
            for j in range(id):childs[j]._fix_width(child)
            break
    if not child is None:
        for i in range(id+1,len(childs)):
            expr_match_width(childs[i],child)
        expr.width = child.width
    else:expr.width = None
def calc_width_s_xi(expr):
    width = 0
    for child in expr.childs:
        expr_match_width(child)
        width+= child.width
    expr.width = width
def calc_width_p_xn(expr):
    expr_match_width(expr.rhs)
    expr.width = expr.rhs.width*expr.count
def calc_width_fetch(expr):
    if expr.lhs.length>1:expr.width = len(expr.lhs)
    else:expr.width = len(expr.rhs)
def calc_width_x_1xx(expr):
    calc_width_x_xx(expr)
    expr.cond._fix_width(1)
def calc_width_x_1x(expr):
    calc_width_x_x(expr)
    expr.lhs._fix_width(1)
expr_width_calc_funcs = {
        'const'  :calc_width_,
        'wire'   :calc_width_,
        'reg'    :calc_width_,
        '~'      :calc_width_x_x,
        '!'      :calc_width_x_x,
        ' -'     :calc_width_x_x,
        ' &'     :calc_width_1_x,
        ' |'     :calc_width_1_x,
        ' ^'     :calc_width_1_x,
        '-'      :calc_width_x_xx,
        '<<'     :calc_width_x_xy,
        '>>'     :calc_width_x_xy,
        '/'      :calc_width_x_xx,
        '%'      :calc_width_x_xx,
        '=='     :calc_width_1_xx,
        '!='     :calc_width_1_xx,
        '<'      :calc_width_1_xx,
        '>'      :calc_width_1_xx,
        '>='     :calc_width_1_xx,
        '<='     :calc_width_1_xx,
        '+'      :calc_width_x_xi,
        '&'      :calc_width_x_xi,
        '&&'     :calc_width_x_xi,
        '|'      :calc_width_x_xi,
        '||'     :calc_width_x_xi,
        '^'      :calc_width_x_xi,
        '{}'     :calc_width_s_xi,
        '*'      :calc_width_x_xx,
        '{{}}'   :calc_width_p_xn,
        '[]'     :calc_width_fetch,
        '?:'     :calc_width_x_1xx,
        'validif':calc_width_x_1x}
expr_width_fix_funcs = {
        'const'  :fix_width_x,
        'wire'   :fix_width_x,
        'reg'    :fix_width_x,
        '~'      :fix_width_x_x,
        '!'      :fix_width_x_x,
        ' -'     :fix_width_x_x,
        ' &'     :fix_width_1_x,
        ' |'     :fix_width_1_x,
        ' ^'     :fix_width_1_x,
        '-'      :fix_width_x_xx,
        '<<'     :fix_width_x_xy,
        '>>'     :fix_width_x_xy,
        '/'      :fix_width_x_xx,
        '%'      :fix_width_x_xx,
        '=='     :fix_width_1_xx,
        '!='     :fix_width_1_xx,
        '<'      :fix_width_1_xx,
        '>'      :fix_width_1_xx,
        '>='     :fix_width_1_xx,
        '<='     :fix_width_1_xx,
        '+'      :fix_width_x_xi,
        '&'      :fix_width_x_xi,
        '&&'     :fix_width_x_xi,
        '|'      :fix_width_x_xi,
        '||'     :fix_width_x_xi,
        '^'      :fix_width_x_xi,
        '{}'     :fix_width_s_xi,
        '*'      :fix_width_x_xx,
        '{{}}'   :fix_width_p_xn,
        '[]'     :fix_width_fetch,
        '?:'     :fix_width_x_xx,
        'validif':fix_width_x_x}