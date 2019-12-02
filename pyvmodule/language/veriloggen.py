#----------------------------------------------------------------------
#pyvmodule:veriloggen.py
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
from .codegen import *
from pyvmodule.expr import *
from pyvmodule.vmodule import VModule
from pyvmodule.check import VChecker
import warnings
from typing import List
class VerilogGen(CodeGen):
    io_details = {'input':'// I, ','output':'// O, ','inout':'// X, '}
    braket_levels = {
        'less':lambda sub,top:sub> top,
        'more':lambda sub,top:sub>=top,
        'full':lambda sub,top:True}
    lines_show_pairing = 10
    cols_spliting_line = 80
    def gen_comments(self,comments:List[str],indent=0)->List[str]:
        lines = []
        myindent = '    '*indent
        for comment in comments:
            for line in comment.split('\n'):
                if line=='':
                    lines.append('')
                    continue
                if line[:2]!='//':
                    line = '// '+line
                lines.append(myindent+line)
        return lines
    def __init__(self):
        self.remap_mul_cat = True
        self.iterations = 0
    def gen(self,obj:'VModuleMeta'):
        self.module = obj
        self.extract()
        lines = []
        lines.extend(self.gen_comments(obj.copyright))
        lines.extend(self.gen_head())
        lines.extend(self.gen_comments(obj.comments))
        lines.extend(self.gen_decl())
        lines.extend(self.gen_assignments())
        lines.extend(self.gen_controlblks())
        lines.extend(self.gen_modules())
        if hasattr(self.module.mydict,'extra_codes'):
            if len(self.module.mydict.extra_codes)>0:
                warnings.warn('Verilog code string inserted.')
            lines.extend(self.module.mydict.extra_codes)
        lines.extend(self.gen_tail())
        return '\n'.join(lines)
    def auto_aligning(self,code_mat):
        rows = len(code_mat)
        if rows<=0:
            return []
        cols = len(code_mat[0])
        align_mat = [[] for i in range(rows)]
        lengths = [0 for i in range(rows)]
        max_length = 0
        max_length_next = 0
        for j in range(cols):
            for i in range(rows):
                padding = max_length-lengths[i]
                part = code_mat[i][j]
                align_mat[i].append(' '*padding+part)
                lengths[i] = max_length+len(part)
                max_length_next = max(max_length_next,lengths[i])
            max_length = max_length_next
        return [''.join(line)  for line in align_mat]
    
    def gen_decl_code_mat(self,ws,indent=0):
        code_mat = []
        for w in ws:
            code_mat.append(self.gen_decl_wire(w))
            code_mat[-1][0:0] = ['    ']*indent
            is_nc = w.io!='input' and w.name.lower() not in self.connected
            code_mat[-1].append('// unconnected' if is_nc else '')
        return code_mat
    def gen_head(self)->List[str]:
        if len(self.ports)<=0:
            return ['module %s();'%self.module.name]
        lines = ['module %s('%self.module.name]
        code_mat = self.gen_decl_code_mat(self.ports,indent=1)
        rows = len(code_mat)
        for i in range(rows-1):
            code_mat[i].insert(-1,',')
        code_mat[-1].insert(-1,'')
        code_mat = self.auto_aligning(code_mat)
        for i in range(rows):
            comments = self.gen_comments(self.ports[i].comments,1)
            if i==0 and len(comments)>0:
                if comments[0]=='':
                    comments.pop(0)
            lines.extend(comments)
            if len(self.ports[i].pragmas)>0:
                raise NotImplementedError('synthesis pragma for port is not implemented.')
            lines.append(code_mat[i])
        lines.append(');')
        return lines
    def gen_pragmas(self,pragmas):
        return [self.gen_pragma(*pragma) for pragma in pragmas.items()]
    def gen_pragma(self,key,val):
        if isinstance(val,str):
            return '(* %s = "%s" *)'%(key,val)
        if isinstance(val,int):
            return '(* %s = %d *)'%(key,val)
        if isinstance(val,bool):
            if val:
                return '(* %s *)'%key
        if val==None:
            return '(* %s *)'%key
        raise TypeError()
    def gen_decl_zip_comments(self,code_mat,ws):
        lines = []
        code_mat = self.auto_aligning(code_mat)
        rows = len(code_mat)
        for i in range(rows):
            wire = ws[i]
            lines.extend(self.gen_comments(wire.comments,0))
            lines.extend(self.gen_pragmas(wire.pragmas))
            lines.append(code_mat[i])
        return lines
    def gen_decl(self)->List[str]:
        lines = []
        code_mat = self.gen_decl_code_mat(self.wires)
        lines.extend(self.gen_decl_zip_comments(code_mat,self.wires))
        code_mat = self.gen_decl_code_mat(self.rams)
        lines.extend(self.gen_decl_zip_comments(code_mat,self.rams))
        return lines
    def gen_expr_comments(self,expr,indent=0):
        if isinstance(expr,Wire):
            return []
        return self.gen_comments(expr.comments,indent)
    def gen_assignments(self)->List[str]:
        code_mat = []
        comments = []
        expr_mat = []
        lines = []
        def output_buffer(code_mat,comments,expr_mat):
            lines = []
            temp = code_mat
            code_mat = self.auto_aligning(code_mat)
            for k in range(len(code_mat)):
                lines.extend(comments[k])
                lines.append(code_mat[k]+expr_mat[k])
            temp.clear()
            comments.clear()
            expr_mat.clear()
            return lines
        for w in self.assignments:
            for key,val in w.assignments:
                code_rows = self.gen_expr(w[key],indent=1)
                code_rows[0].insert(0,'assign ')
                code_rows[-1].append(' = ')
                expr_rows = self.gen_expr(val,indent=1)
                expr_rows[-1].append(';')
                expr_rows = [''.join(expr_row) for expr_row in expr_rows]
                prev_cont = True
                next_cont = True
                if len(code_rows)>1:
                    prev_cont = False
                    next_cont = False
                if len(expr_rows)>1:
                    next_cont = False
                if len(code_mat)>0 and len(code_rows[0])!=len(code_mat[0]):
                    prev_cont = False
                if not prev_cont and not next_cont:
                    lines.extend(output_buffer(code_mat,comments,expr_mat))
                    # output this one
                    code_rows = [''.join(code_row) for code_row in code_rows]
                    lines.extend(self.gen_expr_comments(val))
                    lines.extend(code_rows[:-1])
                    if len(expr_rows)>1:
                        lines.append(code_rows[-1])
                        lines.append('    '+expr_rows[0])
                        lines.extend(expr_rows[1:-1])
                        lines.append(expr_rows[-1])
                    else:
                        lines.append(code_rows[-1]+expr_rows[0])
                else:
                    if not prev_cont:
                        lines.extend(output_buffer(code_mat,comments,expr_mat))
                    comments.append(self.gen_expr_comments(val))
                    code_mat.extend(code_rows)
                    if not next_cont:
                        expr_mat.append('')
                        lines.extend(output_buffer(code_mat,comments,expr_mat))
                        lines.append('    '+expr_rows[0])
                        lines.extend(expr_rows[1:])
                    else:
                        expr_mat.append(expr_rows[0])
        code_mat = self.auto_aligning(code_mat)
        for k in range(len(code_mat)):
            lines.extend(comments[k])
            lines.append(code_mat[k]+expr_mat[k])
        return lines
    def gen_controlblks(self)->List[str]:
        lines = []
        for obj in self.controlblks:
            for key,val in obj.assignments:
                lines.extend(self.gen_expr_comments(val,0))
                lines.extend(self.gen_cblk(val,obj[key]))
        return lines
    def gen_tail(self)->List[str]:
        return ['endmodule // '+self.module.name]
    def receive_object(self,obj):
        if not isinstance(obj,(VModule,Wire)):
            return None,False
        name = obj.name.lower()
        if name in self.module.names:
            pre = self.module.names[name]
            if obj is pre:
                return name,False
            if pre.name!=obj.name:
                raise RuntimeError('"%s" and "%s" are too similar.'%(pre.name,obj.name))
            else:
                raise RuntimeError('Redefined %s "%s".'%(obj.typename,obj.name))
        self.module.names[name] = obj
        return name,True
    def extract_decl(self,val):
        if val.io!=None:
            self.ports.append(val)
        elif val.length>1:
            self.rams.append(val)
        else:
            self.wires.append(val)
    def extract_stmt(self,val):
        if val.typename=='reg':
            self.controlblks.append(val)
        else:
            self.assignments.append(val)
    def extract_item(self,val):
        if isinstance(val,list):
            if len(val)>0:
                if hasattr(val,'comments'):
                    val[0].comments[:0] = val.comments
                for subval in val:
                    self.extract_item(subval)
            return
        name,valid = self.receive_object(val)
        if not valid:
            return
        if isinstance(val,Wire):
            self.extract_decl(val)
            self.extract_stmt(val)
            if len(val.assignments)>0 or val.io=='input':
                self.connected.add(name)
        elif isinstance(val,VModule):
            self.modules.append(val)
            cls = type(val)
            for name,attr in val.__dict__.items():
                if not isinstance(attr,Wire) or name[0]=='_':
                    continue
                assert hasattr(cls,name)
                p = getattr(cls,name)
                assert p.io!=None
                if p.io in {'inout','output'}:
                    self.connected.add(attr.name.lower())
    def extract(self):
        self.module.names = {}
        self.wires = []
        self.rams = []
        self.modules = []
        self.ports = []
        self.assignments = []
        self.controlblks = []
        self.connected = set()
        for key,val in self.module.mydict.items():
            self.extract_item(val)
        return
    def gen_decl_wire(self,obj:Wire)->List[str]:
        columns = []
        assert obj.typename in {'reg','wire'}
        assert obj.width!=None
        if obj.io!=None:
            assert obj.length<=1
            assert obj.io in {'input','output','inout'}
            columns.append(obj.io.ljust(6)+' ')
        columns.append(obj.typename.ljust(4))
        if obj.width!=1:
            columns.extend([' [',str(obj.width-1),':0]'])
        else:
            columns.extend(['','',''])
        columns.append(' '+obj.name)
        if obj.length>1:
            columns.extend(['[',str(obj.length-1),':0]'])
        if obj.io==None:
            columns.append(';')
        return columns
    def gen_cblk_body(self,obj,target,indent=0)->List[str]:
        lines = []
        if isinstance(obj,Expr):
            lines.extend(self.gen_expr_comments(obj,indent))
        if isinstance(obj,ControlBlock):
            lines.extend(self.gen_cblk(obj,target,indent=indent))
        else:
            expr_lines = self.gen_expr(obj,indent=indent+1)
            expr_lines[0][0:0] = ['    '*indent,str(target),'<=']
            expr_lines[-1].append(';')
            expr_lines = [''.join(expr_line) for expr_line in expr_lines]
            lines.extend(expr_lines)
        return lines
    def append_inline(self,target,source):
        if isinstance(source,str):
            target[-1].append(source)
        elif isinstance(source[0],list):
            target[-1].extend(source[0])
            target.extend(source[1:])
        else:
            report__unhandled_type(source)
    width_n_to_width_1_exprs = {'&':'&&','|':'||','~':'!'}
    def gen_braket(self,typename,subexpr,indent,level='less'):
        items = self.gen_expr(subexpr,indent=indent)
        if isinstance(subexpr,Expr):
            if VerilogGen.braket_levels[level](VerilogGen.precedences[self.remap_expr(subexpr)],VerilogGen.precedences[typename]):
                items[0].insert(0,'(')
                items[-1].append(')')
        return items
    def remap_expr(self,obj):
        if obj.typename in VerilogGen.width_n_to_width_1_exprs and len(obj)==1:
            return VerilogGen.width_n_to_width_1_exprs[obj.typename]
        if obj.typename == '*':
            if self.remap_mul_cat:
                return '{}'
            else:
                return '*'
        if obj.typename == '**':
            return '{{}}'
        return obj.typename
    def gen_mux(self,obj,indent=0):
        contents = [[]]
        cond = self.gen_braket('?:',obj.cond,indent)
        lhs = self.gen_braket('?:',obj.lhs,indent+1)
        self.append_inline(contents,cond)
        self.append_inline(contents,' ? ')
        self.append_inline(contents,lhs)
        self.append_inline(contents,' : ')
        return contents
    def gen_expr(self,obj:Expr,indent=0)->List[List[str]]:
        def is_long(*args):
            for arg in args:
                if len(arg)>1:
                    return True
            length = 0
            for arg in args:
                for line in arg:
                    for word in line:
                        length+=len(word)
            return length>VerilogGen.cols_spliting_line
        def extrace_subexpr(obj):
            stack = [obj]
            exprs = []
            typename = self.remap_expr(obj)
            while len(stack)>0:
                top = stack.pop()
                while top.typename==obj.typename:
                    stack.append(top.rhs)
                    top = top.lhs
                exprs.append(self.gen_braket(typename,top,indent=indent+1))
            return exprs
        def joining_subexpr(exprs,spliter,long):
            contents = exprs[0]
            for i in range(1,len(exprs)):
                exprs[i][0].insert(0,spliter)
            if long:
                for i in range(1,len(exprs)):
                    contents.extend(exprs[i])
            else:
                for i in range(1,len(exprs)):
                    contents[-1].extend(exprs[i][0])
            return contents
        assert isinstance(obj,ASTNode)
        typename = self.remap_expr(obj)
        if typename in {'const','wire','reg','range'}:
            if typename in {'wire','reg'} and obj._nameless:
                warnings.warn('Detected nameless wire definition.')
            return [[str(obj)]]
        if typename in {'~','!',' ',' -',' &',' |'}:
            rhs = self.gen_braket(typename,obj.rhs,indent=indent,level='more')
            rhs[0].insert(0,typename)
            return rhs
        myindent = '    '*indent
        if typename in {'-','<<','>>','==','!=','<','>','>=','<=','+','&','&&','|','||','^','*'}:
            if typename in {'+','&','&&','|','||','^','*'}:
                exprs = extrace_subexpr(obj)
                long = obj.long
            else:
                lhs = self.gen_braket(typename,obj.lhs,indent,level='less' if typename in {'-'} else 'more')
                rhs = self.gen_braket(typename,obj.rhs,indent+1,level='more')
                exprs = [lhs,rhs]
                long = False
            long = long or is_long(*exprs)
            if long:
                spliter = myindent+typename
            else:
                spliter = ' '+typename+' '
            contents = joining_subexpr(exprs,spliter,long)
            return contents
        elif typename == '{}':
            exprs = []
            for child in obj.childs:
                exprs.append(self.gen_expr(child,indent=indent+1))
            exprs.reverse()
            long = obj.long or is_long(*exprs)
            if long:
                spliter = myindent+','
            else:
                spliter = ','
            contents = joining_subexpr(exprs,spliter,long)
            contents[0].insert(0,'{')
            contents[-1].append('}')
            return contents
        elif typename == '?:':
            contents = self.gen_mux(obj,indent=indent)
            expr = obj.rhs
             
            while expr.typename=='?:':
                self.iterations+=1
                next = self.gen_mux(expr,indent=indent)
                expr = expr.rhs
                contents.append([myindent])
                self.append_inline(contents,next)
            rhs = self.gen_expr(expr,indent=indent+1)
            self.append_inline(contents,rhs)
            return contents
        if typename in {'[]'}:
            contents = [[str(obj.lhs),'[']]
            if obj.rhs.typename=='const':
                contents[-1].extend([str(int(obj.rhs)),']'])
            elif obj.rhs.typename=='range':
                assert obj.rhs.step==1
                if obj.rhs.stop==obj.rhs.start+1:
                    contents[-1].extend(['','',str(int(obj.rhs.start)),']'])
                else:
                    contents[-1].extend([str(obj.rhs.stop-1),':',str(obj.rhs.start),']'])
            elif isinstance(obj.rhs,ASTNode):
                self.append_inline(contents,self.gen_expr(obj.rhs,indent=indent+1))
                contents[-1].append(']')
            else:
                raise NotImplementedError()
            return contents
        if typename in {'{{}}'}:
            contents = self.gen_expr(obj.lhs,indent=indent)
            contents[0][0:0] = ['{',str(int(obj.rhs)),'{']
            contents[-1].append('}}')
            return contents
        raise TypeError('Unrecongnized operator "%s"'%obj.typename)
    def gen_cblk(self,obj:ControlBlock,target:Wire,indent=0)->List[str]:
        if obj.lhs == None:
            raise RuntimeError('"%s" block with empty body.')
        lines = []
        myindent = '    '*indent
        if obj.typename in {'always@','if'}:
            if obj.cond!=None:
                cond_lines = self.gen_expr(obj.cond,indent=indent+1)
                if obj.typename=='always@':
                    if obj.edge!=None:
                        cond_lines[0].insert(0,' ')
                        cond_lines[0].insert(0,obj.edge)
                    cond_lines[0].insert(0,'always@(')
                else:
                    assert obj.typename=='if'
                    cond_lines[0].insert(0,'if(')
                    cond_lines[0].insert(0,'    '*indent)
                cond_lines[-1].append(')')
            else:
                cond_lines = [['always@(*)']]
            cond_lines = [''.join(cond_line) for cond_line in cond_lines]
            lines.extend(cond_lines)
        elif obj.typename=='always#':
            lines.append('always #%d'%obj.delay)
        elif obj.typename=='initial':
            lines.append('initial')
        elif not obj.typename=='else':
            report__unhandled_type(obj)
        begin_line = ''.join(([myindent,'begin',':',obj.name] if obj.name!=None else [myindent,'begin']))
        contents = self.gen_cblk_body(obj.lhs,target,indent=indent+1)
        end_line = myindent+'end'
        if len(contents)>VerilogGen.lines_show_pairing:
            if obj.typename=='else':
                if__condition_comment = ('\n'+myindent+'// ').join(str(obj.cond_if).split('\n'))
                begin_line += ' // !(%s)'%if__condition_comment
                end_line   += ' // else - if(%s)'%if__condition_comment
            elif obj.typename=='if':
                end_line+='// '
                end_line+=('\n'+myindent+'// ').join(if_cond.split('\n'))
        lines.append(begin_line)
        lines.extend(contents)
        lines.append(end_line)
        if obj.next!=None:
            if obj.typename=='if':
                lines.append(myindent+'else')
            lines.extend(self.gen_cblk(obj.next,target,indent=indent))
        return lines
    def gen_modules(self)->List[str]:
        lines = []
        code_mat = []
        comments = []
        io_infos = []
        for module in self.modules:
            lines.extend(self.gen_comments(module.comments,0))
            cls = type(module)
            name = module.name
            for val in module.ports():
                io_infos.append([self.io_details[val.io],str(len(val))])
                comments.append(self.gen_comments(val.comments,1))
                code_row = ['    .']
                code_row.append(val.name)
                code_row.append('(')
                if val.name in module.__dict__:
                    code_row.append(str(module.__dict__[val.name]))
                else:
                    warnings.warn('Port "%s" of module "%s" is unconnected.'%(val.name,name))
                    code_row.append('')
                code_row.append(')')
                code_mat.append(code_row)
            rows = len(code_mat)
            for i in range(rows):
                if i+1==rows:
                    code_mat[i].append('')
                else:
                    code_mat[i].append(',')
                code_mat[i].extend(io_infos[i])
            code_mat = self.auto_aligning(code_mat)
            if rows<=0:
                warnings.warn('No port defined in module "%s".'%cls.name)
                lines.append('%s %s();'%(cls.name,name))
            else:
                lines.append('%s %s'%(cls.name,name))
                lines.append('(')
                for i in range(rows):
                    lines.extend(comments[i])
                    lines.append(''.join(code_mat[i]))
                lines.append(');')
            code_mat.clear()
            comments.clear()
            io_infos.clear()
        return lines