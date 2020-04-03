import sys
import os
vmodule_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../..')
cur_path =  set(sys.path)
if vmodule_dir not in cur_path:
    sys.path.insert(0,vmodule_dir)
from pyvmodule.develope import *
class counter1(VModule):
    name = 'Counter'
    comments.append('example -- a simple counter.')
    clock = Wire(io='input')
    reset = Wire(io='input')
    valid = Wire(io='input')
    valid.comments.append('Enable signal for counter.')
    cnt = Reg(4,io='output')
    expr = cnt+1
    cnt_next = Wire(expr)
    when_ok = When(valid)[cnt_next]
    cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
class counter2(VModule):
    name = 'Counter'
    comments.append('example -- a simple counter.')
    clock = Wire(io='input')
    reset = Wire(io='input')
    valid = Wire(io='input')
    cnt = Reg(4)
    cnt.next = Wire(cnt+1)
    cnt.io='output'
    valid.comments.append('Enable signal for counter.')
    when_ok = When(valid)[cnt_next]
    cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
class counter3(VModule):
    name = 'Counter'
    comments.append('example -- a simple counter.')
    clock = Wire(io='input')
    reset = Wire(io='input')
    valid = Wire(io='input')
    cnt = Reg(4)
    cnt.next = Wire(cnt+1)
    cnt.next.prev = cnt
    cnt.io='output'
    valid.comments.append('Enable signal for counter.')
    when_ok = When(valid)[cnt_next]
    cnt[:] = Always(clock)[When(reset)[0].Otherwise[when_ok]]
class counter4(VModule):
    name = 'Counter'
    comments.append('example -- a simple counter.')
    clock = Wire(io='input')
    reset = Wire(io='input')
    valid = Wire(io='input')
    cnt = Reg(4)
    cnt.next = Wire(cnt+1)
    cnt.io='output'
    valid.comments.append('Enable signal for counter.')
    when_ok = When(valid)[cnt_next]
    cnt[:] = When(reset)[0].Otherwise[when_ok]
def test_gen(m,name,testname,test_id=[0],ans=None):
    test_id[0]+=1
    if testname is None:testname = 'Test %d'%test_id[0]
    try:
        code = m.save(dir=sys.stdout)[name]
    except Exception:
        print('// '+testname+' error')
        return
    if ans is None:print('// '+testname+' passed')
    elif ans!=code:
        ans_lines = ans.split('\n')
        cod_lines = code.split('\n')
        for i in range(max(len(ans_lines),len(cod_lines))):
            if i>=len(ans_lines):print('Extra line generation.')
            elif i>=len(cod_lines):print('Missing line generation')
            elif ans_lines[i]!=cod_lines[i]:
                print('Unmatched code at line %d, .\n>>>expecting:\n%s\n>>>generated:\n%s'%(i,ans_lines[i],cod_lines[i]))
            else:continue
            break
        print('// '+testname+' failed')
    else:print('// '+testname+' passed')
    return code
if __name__ == '__main__':
    ans = test_gen(counter1,'Counter','Test base')
    test_gen(counter2,'Counter','Test attr',ans=ans)
    test_gen(counter3,'Counter','Test attr-self',ans=ans)
    test_gen(counter4,'Counter','Test hidden-clock',ans=ans)