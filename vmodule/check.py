#----------------------------------------------------------------------
#pyvmodule:check.py
#
#Copyright (C) 2019  Hong Ze Tan
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.
#----------------------------------------------------------------------
from .ast import ASTNode
import warnings
class VChecker:
    width_1_to_width_n_exprs = {'&&':'&','||':'|','!':'~'}
    
    control_blocks = {
        'always@','always#','initial',
        'if','else','case'}
    fetchable_typenames = {'wire','reg'}
    atom_typename = {'const'}|fetchable_typenames
    unary_operators = {'~','!',' ',' -',' &',' ^',' |'}
    
    abelian_operators = {'+','&','^','|','&&','||'}
    width_matching_operators = abelian_operators|{'-','?:'}
    compare_operators = {'<=','<','>=','>','==','!='}
    shift_operators = {'<<','>>','<<<','>>>'}
    binary_operators = abelian_operators|{'-'}|compare_operators|shift_operators
    other_operators = {
        '[]','*','{}','{{}}',
        '?:'}
    possible_typenames = control_blocks|atom_typename|unary_operators|binary_operators|other_operators
    verilog_keywords = {'begin','end','always','initial','generate','endgenerate','if','else','for','genvar','wire','reg','module','endmodule','input','output','inout','assign','case','endcase'}
    def identifier(name):
        if name==None:
            return None
        if not isinstance(name,str):
            raise TypeError('Name must be a string, not .'%str(type(name)))
        if len(name)>32:
            raise KeyError('Name "%s" is too long.'%name)
        if len(name)<=0:
            raise KeyError('Name must not be empty.')
        if not name[0].isalpha():
            raise KeyError('Name "%s" must not start with "%s"'%(name,name[0]))
        if not name[-1].isalnum():
            raise KeyError('Name "%s" must not end with "%s"'%(name,name[-1]))
        for i in range(len(name)):
            c = name[i]
            if c.isalnum():
                continue
            if c=='_':
                if name[i+1]=='_':
                    raise KeyError('"_" must not be consecutive.')
                continue
            raise KeyError('Invalid character "%s"'%c)
        if name in VChecker.verilog_keywords:
            raise KeyError('Name must not be a verilog keyword.')
        return name
    def port(io,length,typename):
        if io not in {None,'input','output','inout'}:
            assert isinstance(io,str)
            raise ValueError('Undefined port type "%s"'%io)
        elif io not in {None,'output'}:
            if typename=='reg':
                raise RuntimeError('"reg" type must not be input signal.')
        if io!=None and length>1:
            raise ValueError('RAM could not be port.')
        return io
    def shape(width,length):
        if width==1 and length>1:
            warnings.warn('Suspicious declaration, do you mean "width=%d".'%length)
            return length,width
        else:
            return width,length
    def index(i,maxrange,allow_eq=False):
        if i>maxrange:
            raise IndexError('Index out of range.')
        if i==maxrange and not allow_eq:
            raise IndexError('Index out of range.')
        if i<0:
            raise IndexError('Negative index')
    def match(source=None,expected=None):
        def get_width(target):
            if target==None:
                return None
            if isinstance(target,int):
                return target
            if isinstance(target,ASTNode):
                return target.width
            raise NotImplementedError()
        def report_negative(target):
            if isinstance(target,ASTNode):
                raise ValueError('Unexpected non-positive width %d of "%s".'%(len(target),str(target)))
            else:
                raise ValueError('Unexpected non-positive width %d.'%target)
        def get_info(target):
            if isinstance(target,int):
                return 'width %d'%target
            else:
                return '"%s"(width=%d)'%(str(target),len(target))
        source_width = get_width(source)
        expect_width = get_width(expected)
        if source_width!=None and source_width<=0:
            report_negative(source)
        if expect_width!=None and expect_width<=0:
            report_negative(expected)
        if source_width==None and expect_width==None:
            if source!=None:
                raise ValueError('Width of "%s" is undetermined .'%str(source))
            else:
                raise ValueError('Undetermined width.')
        elif expect_width==None:
            # do not need check
            return
        elif source_width==None:
            # fix the width with the expected
            source.width = expect_width
            return
        elif source_width!=expect_width:
            source_info = get_info(source)
            expect_info = get_info(expected)
            raise ValueError('%s unmatches %s'%(source_info,expect_info))
        else:
            # passed check
            return
    def fix_width(expr,expected):
        assert isinstance(expr,ASTNode)
        if expr.typename not in VChecker.possible_typenames:
            raise ValueError('Unrecognized operator "%s".'%expr.typename)
        VChecker.match(expr,expected)
        if expr.typename in VChecker.width_matching_operators:
            VChecker.fix_width(expr.lhs,expected)
            VChecker.fix_width(expr.rhs,expected)
        if expr.typename in VChecker.unary_operators:
            if expr.typename in {' |',' &',' ^'}:
                VChecker.fix_width(expr.rhs,None)
            else:
                VChecker.fix_width(expr.rhs,expected)
        if expr.typename in VChecker.shift_operators:
            VChecker.fix_width(expr.lhs.expected)
            if expr.lhs.width<(1<<expr.rhs.width):
                warnings.warn('Shifting operand is too wide.')
        if expr.typename == '[]':
            if expr.rhs.typename=='range':
                VChecker.index(int(expr.rhs.start),len(expr.lhs),allow_eq=False)
                VChecker.index(int(expr.rhs.stop),len(expr.lhs),allow_eq=True)
            else:
                maxrange = expr.lhs.length if expr.lhs.length>1 else expr.lhs.width
                if expr.rhs.typename=='const':
                    VChecker.index(int(expr.rhs),maxrange)
                else:
                    VChecker.match(expr.rhs)
                    if maxrange<(1<<expr.rhs.width):
                        warnings.warn('Index operand is too wide.')
                    if maxrange>(1<<expr.rhs.width):
                        warnings.warn('Index operand is too narrow.')
        if expr.typename == 'const':
            expr.cut__off()
        if expr.typename in VChecker.control_blocks:
            if expr.rhs!=None:
                VChecker.fix_width(expr.rhs,expected)
            if expr.lhs!=None:
                VChecker.fix_width(expr.lhs,expected)
    def unhandled_type(obj):
        raise TypeError('Unhandled type "%s". '%str(type(obj)))