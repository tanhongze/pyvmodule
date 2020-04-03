import unittest
from pyvmodule.develope import *
from pyvmodule.exceptions import *
def remove_format(s):return s.replace(' ','').replace('\n','')
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
class TestAutoConnect(unittest.TestCase):
    def module_case(self,m,s):self.assertEqual(remove_format(str(m)),remove_format(s))
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
            auto_connect(enc,'di',name='inter')
            auto_connect(enc,'do',name='do')
        self.module_case(Top,top_decoder_encoder_code)