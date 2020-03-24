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
def remove_format(s):return s.replace(' ','').replace('\n','')
decoder_8_code = \
'''
module Decoder(
    input  wire [2:0] i_d,
    output wire [7:0] o_d
);
assign o_d[0] = i_d == 3'h0;
assign o_d[1] = i_d == 3'h1;
assign o_d[2] = i_d == 3'h2;
assign o_d[3] = i_d == 3'h3;
assign o_d[4] = i_d == 3'h4;
assign o_d[5] = i_d == 3'h5;
assign o_d[6] = i_d == 3'h6;
assign o_d[7] = i_d == 3'h7;
endmodule // Decoder
'''
class TestVerilog(unittest.TestCase):
    def module_case(self,m,s):self.assertEqual(remove_format(str(m)),remove_format(s))
    def test_module_decoder_32(self):
        class Decoder(VModule[['i_d.i3','o_d.o8']]):
            for i in range(len(o_d)):
                o_d[i] = i_d.equal_to(i)
        self.module_case(Decoder,decoder_8_code)
if __name__ == '__main__':
    unittest.main(verbosity=2)