#coding: UTF-8
import pytest
from pyvmodule.develope import *
def test_expr1():
    a = Wire(width=1,name='a')
    assert str( a) == 'a'
    assert str(~a) == '!a'
