import sys
import os
vmodule_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../..')
cur_path =  set(sys.path)
if vmodule_dir not in cur_path:
    sys.path.insert(0,vmodule_dir)
import unittest
from pyvmodule.develope import *
from pyvmodule.exceptions import *
from functools import reduce
class TestVerilog(unittest.TestCase):
    def expr_case(self,e,repre,width):
        self.assertEqual(str(e),repre)
        self.assertEqual(len(e),width)
    def const_case(self,e,repre,width,value):
        self.assertEqual(str(e),repre)
        self.assertEqual(int(e),value)
        self.assertEqual(len(e),width)
    def checkStrName(self,obj,ans):self.assertEqual((str(obj),obj.name),(ans,ans))
    def checkName   (self,obj,ans):self.assertEqual(obj.name,ans)
    def a(self,*v):return Wire(*v,name='a')
    def b(self,*v):return Wire(*v,name='b')
    def c(self,*v):return Wire(*v,name='c')
    def x(self,*v):return Wire(*v,name='x')
    def y(self,*v):return Wire(*v,name='y')
    def z(self,*v):return Wire(*v,name='z')
    def hex(self,value,width):return Hex(value,width=width)
    def test_name_wire_raise_start(self):
        with self.assertRaises(NameError):x = Wire(name='_x')
    def test_name_wire_end      (self):
        with self.assertRaises(NameError):x = Wire(name='x_')
    def test_name_wire_underline(self):
        with self.assertRaises(NameError):x = Wire(name='x__y')
    def test_name_wire_number(self):
        with self.assertRaises(NameError):x = Wire(name='1')
    def test_name_wire_special_char(self):
        with self.assertRaises(NameError):x = Wire(name='$')
    def test_name_wire_white_char(self):
        with self.assertRaises(NameError):x = Wire(name=' ')
    def test_name_wire_empty_str(self):
        with self.assertRaises(NameError):x = Wire(name='')
    def test_name_wire_long_sting(self):
        with self.assertRaises(NameError):x = Wire(name='the_identifier_with_a_really_long_name_that_longer_than_32_characters')
    def test_name_wire_normal_1(self):self.checkStrName(Wire(name='x'),'x')
    def test_name_wire_normal_2(self):self.checkStrName(Wire(name='base'),'base')
    def test_name_wire_ssa_enable(self):
        base = Wire(name='base')
        base.enable_ssa('ins')
        for i in range(3):
            base.ins = Wire(i+1)
            self.expr_case(base.inss[i],'base_ins%d'%i,i+1)
            self.expr_case(base.ins,'base_ins%d'%i,i+1)
        self.expr_case(base.ins1,'base_ins1',2)
    def test_name_wire_tree_wire_stem_wire_leaf_forward(self):
        base = Wire(name='base')
        self.checkStrName(base,'base')
        base.a = Wire()
        self.checkStrName(base,'base')
        self.checkStrName(base.a,'base_a')
        base.a.b = Wire()
        self.checkStrName(base,'base')
        self.checkStrName(base.a,'base_a')
        self.checkStrName(base.a.b,'base_a_b')
        self.checkStrName(base.a_b,'base_a_b')
    def test_name_wire_tree_wire_stem_wire_leaf_backward(self):
        b = Wire()
        a = Wire()
        a.b = b
        base = Wire(name='base')
        base.a = a
        self.checkStrName(base,'base')
        self.checkStrName(base.a,'base_a')
        self.checkStrName(base.a.b,'base_a_b')
        self.checkStrName(base.a_b,'base_a_b')
    def test_name_dict_vmod_stem_wire_leaf_wire(self):
        class base(VModule):
            a = Wire()
            a.b = Wire()
            self.checkStrName(a,'a')
            self.checkStrName(a.b,'a_b')
            self.checkStrName(a_b,'a_b')
        self.checkName(base,'base')
        self.checkStrName(base.a,'a')
        self.checkStrName(base.a.b,'a_b')
        self.checkStrName(base.a_b,'a_b')
    def test_name_dict_vmod_tree_wire_leaf_wire(self):
        x = Wire()
        x.b = Wire()
        class base(VModule):
            a = x
            self.checkStrName(a,'a')
            self.checkStrName(a.b,'a_b')
            self.checkStrName(a_b,'a_b')
        x.b.c = Wire()
        self.checkName(base,'base')
        self.checkStrName(base.a,'a')
        self.checkStrName(base.a.b,'a_b')
        self.checkStrName(base.a_b,'a_b')
        self.checkStrName(base.a_b.c,'a_b_c')
        self.checkStrName(base.a_b_c,'a_b_c')
    def test_name_dict_vmod_tree_wire_leaf_wire_reverse(self):
        x = Wire(name='a')
        x.b = Wire()
        class base(VModule):
            b = x.b
        x.c = Wire()
        self.checkStrName(base.a,'a')
        self.checkStrName(base.a_b,'a_b')
        self.checkStrName(base.a_c,'a_c')
    def test_name_dual_dict(self):
        class base1(VModule):
            a = Wire(io='output')
        class base2(VModule):
            b = Wire(io='output')
        base1.a.name = 'c'
        base2.b.name = 'd'
        self.checkStrName(base1.a,'c')
        self.checkStrName(base2.b,'d')
        self.checkStrName(base1.c,'c')
        self.checkStrName(base2.d,'d')
        with self.assertRaises(AttributeError):
            name = base1.b.name
            name = base1.d.name
        with self.assertRaises(AttributeError):
            name = base2.a.name
            name = base2.c.name
    def test_name_tree_loop(self):
        base = Wire(name='base')
        x = Wire()
        x.y = x
        base.x = x
        self.checkStrName(x,'base_x')
    def test_name_tree_rename(self):
        base = Wire(name='base')
        base.a = Wire()
        base.a.b = Wire()
        base.a.name = 'c'
        self.assertEqual(str(base.c.b),'base_c_b')
        base.a.name = 'a'
        self.assertEqual(str(base.a.b),'base_a_b')
    def test_name_dict_instance(self):
        class ins(VModule):
            self.assertEqual(name,'ins')
            name = 'bottom'
            self.assertEqual(name,'bottom')
        self.assertEqual(ins.name,'bottom')
        ins.name = 'ins'
        self.assertEqual(ins.name,'ins')
        class top(VModule):
            a = ins()
            self.assertEqual(a.name,'a')
        self.assertEqual(top.name,'top')
        self.assertEqual(ins.name,'ins')
        self.assertEqual(top.a.name,'a')
    def test_wire_decl_input_w3_list (self):self.assertEqual(''.join(Wire(3,name='a',io='input' )._decl_generate(last=False,mark=False)),'input  wire [2:0] a,')
    def test_wire_decl_input_w3_last (self):self.assertEqual(''.join(Wire(3,name='a',io='input' )._decl_generate(last=True ,mark=False)),'input  wire [2:0] a ')
    def test_wire_decl_input_w1_last (self):self.assertEqual(''.join(Wire(1,name='a',io='input' )._decl_generate(last=True ,mark=False)),'input  wire a ')
    def test_wire_decl_output_w3_last(self):self.assertEqual(''.join(Wire(3,name='a',io='output')._decl_generate(last=True ,mark=False)),'output wire [2:0] a ')
    def test_wire_decl_output_w3_last(self):self.assertEqual(''.join(Reg (3,name='a',io='output')._decl_generate(last=True ,mark=False)),'output reg  [2:0] a ')
    def test_func_cblk(self):
        clock = Wire(name='clock')
        blk = Always(clock)[vfunction.display('a')]
        self.assertEqual(str(blk),'always@(posedge clock)\nbegin\n    $display("a");\nend')
    def test_func_display(self):self.assertEqual(str(vfunction.display('a')),'$display("a")')
    def test_func_time(self):self.assertEqual(str(vfunction.time()),'$time')
    def test_wire_width_default(self):self.expr_case(Wire(name='a'),'a',1)
    def test_wire_width_key    (self):self.expr_case(Wire(name='a',width=3),'a',3)
    def test_wire_width_pass   (self):self.expr_case(Wire(Wire(3),name='a'),'a',3)
    def test_wire_width_short  (self):self.expr_case(Wire(3,name='a'),'a',3)
    def test_wire_width_exprkey(self):self.expr_case(Wire(expr=self.hex(3,3),name='a'),'a',3)
    def test_wire_width_bothkey(self):self.expr_case(Wire(expr=self.hex(3,3),width=3,name='a'),'a',3)
    def test_wire_width_non_zero    (self):
        with self.assertRaises(WidthError):x = Wire( 0,name='x')
    def test_wire_width_non_negative(self):
        with self.assertRaises(WidthError):x = Wire(-1,name='x')
    def test_expr_basic_wire(self):self.expr_case(Wire(name='a',width=8),'a',8)
    def test_expr_basic_lt(self):self.expr_case(self.x(8)< self.y(8),'x < y' ,1)
    def test_expr_basic_le(self):self.expr_case(self.x(8)<=self.y(8),'x <= y',1)
    def test_expr_basic_ge(self):self.expr_case(self.x(8)>=self.y(8),'x >= y',1)
    def test_expr_basic_gt(self):self.expr_case(self.x(8)> self.y(8),'x > y' ,1)
    def test_expr_basic_eq(self):self.expr_case(self.x(8)//self.y(8),'x == y',1)
    def test_expr_basic_ne(self):self.expr_case(self.x(8).not_equal_to(self.y(8)),'x != y',1)
    def test_expr_basic_add(self):self.expr_case(self.x(8)+self.y(8),'x + y',8)
    def test_expr_basic_sub(self):self.expr_case(self.x(8)-self.y(8),'x - y',8)
    def test_expr_basic_xor(self):self.expr_case(self.x(8)^self.y(8),'x ^ y',8)
    def test_expr_basic_and(self):self.expr_case(self.x(8)&self.y(8),'x & y',8)
    def test_expr_basic_or (self):self.expr_case(self.x(8)|self.y(8),'x | y',8)
    def test_expr_basic_not(self):self.expr_case(~self.x(8),'~x',8)
    def test_expr_basic_logic_and(self):self.expr_case(self.x(1)&self.y(1),'x && y',1)
    def test_expr_basic_logic_or (self):self.expr_case(self.x(1)|self.y(1),'x || y',1)
    def test_expr_basic_logic_not(self):self.expr_case(~self.x(1),'!x',1)
    def test_expr_basic_concatenate(self):self.expr_case(self.x(8)*self.y(8),'{y,x}',16)
    def test_expr_basic_replication(self):self.expr_case(self.x(8)**3,'{3{x}}',24)
    def test_expr_basic_multiply(self):self.expr_case(self.x(8).multiply_operate(self.y(8)),'x * y',8)
    def test_expr_basic_divide  (self):self.expr_case(self.x(8).divide_operate(self.y(8)),'x / y',8)
    def test_expr_basic_module  (self):self.expr_case(self.x(8).module_operate(self.y(8)),'x % y',8)
    def test_expr_basic_validif (self):self.expr_case(self.x(8).validif(self.a(1)),'{8{a}} & x',8)
    def test_expr_basic_mux     (self):self.expr_case(self.z(1).mux(self.x(8),self.y(8)),'z ? x : y',8)
    def test_expr_const_prop_add(self):self.const_case(self.hex(1,8)+self.hex(1,8),"8'h2",8,2)
    def test_expr_const_prop_sub(self):self.const_case(self.hex(1,8)-self.hex(1,8),"8'h0",8,0)
    def test_expr_const_prop_xor(self):self.const_case(self.hex(1,8)^self.hex(1,8),"8'h0",8,0)
    def test_expr_const_prop_and(self):self.const_case(self.hex(1,8)&self.hex(1,8),"8'h1",8,1)
    def test_expr_const_prop_or (self):self.const_case(self.hex(1,8)|self.hex(1,8),"8'h1",8,1)
    def test_expr_const_prop_fetch_default_m(self):self.const_case(self.hex(1,8)[:3],"3'h1",3,1)
    def test_expr_const_prop_fetch_m_default(self):self.const_case(self.hex(1,8)[3:],"5'h0",5,0)
    def test_expr_const_prop_concatenate(self):self.const_case(self.hex(1,8)*self.hex(1,8),"16'h101",16,257)
    def test_expr_const_prop_replication(self):self.const_case(self.hex(1,8)**2           ,"16'h101",16,257)
    def test_expr_recur_and_eq_wire_wire_wire(self):self.expr_case(self.a(1)&(self.x(8)//self.y(8)),'a && x == y',1)
    def test_expr_recur_and_wire_eq_wire_wire(self):self.expr_case((self.a(8)&self.x(8))//self.y(8),'(a & x) == y',1)
    def test_expr_recur_land_wire_eq_wire_wire(self):self.expr_case((self.a(1)&self.x(1))//self.y(1),'(a && x) == y',1)
    def test_expr_recur_and_wire_and_wire_wire(self):self.expr_case(self.x(8)&(self.y(8)&self.z(8)),'x & y & z',8)
    def test_expr_recur_and_wire_and_wire_wire(self):self.expr_case((self.x(8)&self.y(8))&self.z(8),'x & y & z',8)
    def test_expr_recur_add_add_wire_wire_wire(self):self.expr_case(self.x(8)+(self.y(8)+self.z(8)),'x + y + z',8)
    def test_expr_recur_add_add_wire_wire_wire(self):self.expr_case((self.x(8)+self.y(8))+self.z(8),'x + y + z',8)
    def test_expr_recur_mux_cond_wire_mux_cond_wire_wire(self):self.expr_case(self.a(1).mux(self.x(8),self.b(1).mux(self.y(8),self.z(8))),'a ? x : \nb ? y : z',8)
    def test_expr_reduce_add(self):self.expr_case(reduce(lambda x,y: x+y, [self.x(8),self.y(8)]),'x + y',8)
    def test_expr_reduce_and(self):self.expr_case(reduce(lambda x,y: x&y, [self.x(8),self.y(8)]),'x & y',8)
    def test_expr_reduce_or (self):self.expr_case(reduce(lambda x,y: x|y, [self.x(8),self.y(8)]),'x | y',8)
    def test_expr_reduce_xor(self):self.expr_case(reduce(lambda x,y: x^y, [self.x(8),self.y(8)]),'x ^ y',8)
    def test_expr_reduce_concatenate(self):self.expr_case(reduce(lambda x,y: x*y, [self.x(8),self.y(8),self.a(1),self.b(1)]),'{b,a,y,x}',18)
if __name__ == '__main__':
    unittest.main(verbosity=2)