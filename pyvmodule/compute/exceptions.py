from pyvmodule.ast import ASTNode
class WidthError(ValueError):
    def get_info(target):return 'width %d'%target if isinstance(target,int) else '"%s"(width=%d)'%(str(target),len(target))
class ImplementError(NotImplementedError):pass
def raise_error(err):raise err
def a_isinstance(x,types):isinstance(x,types) or raise_error(TypeError('Expecting types %s, got %s.'%(str(types),type(x))))
def e_unhandled_type(x):raise_error(TypeError(type(x)))
def a_value_positive(value,name):return value>0 or raise_error(WidthError('%s cannot be non-positive value %d.'%(name,value)))
def a_width_positive(width,value):return width>0 or raise_error( \
    WidthError('Unexpected non-positive width, %s'%WidthError.get_info(value)))
def a_width_match(width1,value1,width2,value2):return width1==width2 or raise_error( \
    WidthError('%s unmatches %s'%(WidthError.get_info(value1),WidthError.get_info(value2))))
def a_part_select_all(w,k):return a_isinstance(key,slice) and key.start is None and key.stop is None and key.step is None or \
    raise_error(KeyError('Invalid part-selection "%s" of "%s".'%(k,w)))
def a_is_astnode(w):return a_isinstance(w,ASTNode)
def a_assign_wire(w):return w.typename == 'wire' or raise_error(TypeError('Cannot assign to "%s" variable "%s"'%(w.typename,w)))
def a_assign_wire_fecth(w):return a_with_typename(w._get_target() if w.typename == '[]' else w,'wire')
def a_assignable(w):return a_is_astnode(w) and a_assign_wire_fecth(w)
