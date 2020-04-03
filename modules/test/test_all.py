import sys
import os
vmodule_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../..')
cur_path =  set(sys.path)
if vmodule_dir not in cur_path:
    sys.path.insert(0,vmodule_dir)
import unittest
from test_verilog import *
from test_tools import *
if __name__ == '__main__':
    unittest.main(verbosity=2)