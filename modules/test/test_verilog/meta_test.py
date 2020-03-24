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
decoder_32_code = \
'''
module Decoder(
    input  wire [4 :0] di,
    output wire [31:0] do
);
assign do[0 ] = di == 5'h0 ;
assign do[1 ] = di == 5'h1 ;
assign do[2 ] = di == 5'h2 ;
assign do[3 ] = di == 5'h3 ;
assign do[4 ] = di == 5'h4 ;
assign do[5 ] = di == 5'h5 ;
assign do[6 ] = di == 5'h6 ;
assign do[7 ] = di == 5'h7 ;
assign do[8 ] = di == 5'h8 ;
assign do[9 ] = di == 5'h9 ;
assign do[10] = di == 5'ha ;
assign do[11] = di == 5'hb ;
assign do[12] = di == 5'hc ;
assign do[13] = di == 5'hd ;
assign do[14] = di == 5'he ;
assign do[15] = di == 5'hf ;
assign do[16] = di == 5'h10;
assign do[17] = di == 5'h11;
assign do[18] = di == 5'h12;
assign do[19] = di == 5'h13;
assign do[20] = di == 5'h14;
assign do[21] = di == 5'h15;
assign do[22] = di == 5'h16;
assign do[23] = di == 5'h17;
assign do[24] = di == 5'h18;
assign do[25] = di == 5'h19;
assign do[26] = di == 5'h1a;
assign do[27] = di == 5'h1b;
assign do[28] = di == 5'h1c;
assign do[29] = di == 5'h1d;
assign do[30] = di == 5'h1e;
assign do[31] = di == 5'h1f;
endmodule // Decoder
'''
encoder_32_code = \
'''
module Encoder(
    input  wire [31:0] di,
    output wire [4 :0] do
);
assign do = {5{di[1 ]}} & 5'h1
          | {5{di[2 ]}} & 5'h2
          | {5{di[3 ]}} & 5'h3
          | {5{di[4 ]}} & 5'h4
          | {5{di[5 ]}} & 5'h5
          | {5{di[6 ]}} & 5'h6
          | {5{di[7 ]}} & 5'h7
          | {5{di[8 ]}} & 5'h8
          | {5{di[9 ]}} & 5'h9
          | {5{di[10]}} & 5'ha
          | {5{di[11]}} & 5'hb
          | {5{di[12]}} & 5'hc
          | {5{di[13]}} & 5'hd
          | {5{di[14]}} & 5'he
          | {5{di[15]}} & 5'hf
          | {5{di[16]}} & 5'h10
          | {5{di[17]}} & 5'h11
          | {5{di[18]}} & 5'h12
          | {5{di[19]}} & 5'h13
          | {5{di[20]}} & 5'h14
          | {5{di[21]}} & 5'h15
          | {5{di[22]}} & 5'h16
          | {5{di[23]}} & 5'h17
          | {5{di[24]}} & 5'h18
          | {5{di[25]}} & 5'h19
          | {5{di[26]}} & 5'h1a
          | {5{di[27]}} & 5'h1b
          | {5{di[28]}} & 5'h1c
          | {5{di[29]}} & 5'h1d
          | {5{di[30]}} & 5'h1e
          | {5{di[31]}};
endmodule // Encoder
'''
top_decoder_encoder_code = \
'''
module Top(
    input  wire [4:0] di,
    output wire [4:0] do
);
wire [31:0] inter;
Decoder dec
(
    .di(di   ),// I, 5
    .do(inter) // O, 32
);
Encoder enc
(
    .di(inter),// I, 32
    .do(do   ) // O, 5
);
endmodule // Top
'''
def remove_format(s):return s.replace(' ','').replace('\n','')
class TestMeta(unittest.TestCase):
    def module_case(self,m,s):self.assertEqual(remove_format(str(m)),remove_format(s))
    def test_module_decoder_32(self):
        class Decoder(VModule):
            di = Wire(5,io='input')
            do = decode(di)
            do.io = 'output'
        self.module_case(Decoder,decoder_32_code)
    def test_module_encoder_32(self):
        class Encoder(VModule):
            di = Wire(32,io='input')
            do = encode(di)
            do.io = 'output'
        self.module_case(Encoder,encoder_32_code)
    def test_module_instance(self):
        class Decoder(VModule):
            di = Wire(5,io='input')
            do = decode(di)
            do.io = 'output'
        class Encoder(VModule):
            di = Wire(32,io='input')
            do = encode(di)
            do.io = 'output'
        class Top(VModule):
            di = Wire(5,io='input')
            do = Wire(5,io='output')
            inter = Wire(32)
            dec = Decoder(di=di,do=inter)
            enc = Encoder()
            enc.di = inter
            enc.do = do
        self.module_case(Top,top_decoder_encoder_code)
        
if __name__ == '__main__':
    unittest.main(verbosity=2)