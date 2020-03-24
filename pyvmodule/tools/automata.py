from pyvmodule.develope import *
import math
__all__ = ['DFA','NFA']
def get_leaf(tree):
    if isinstance(tree,str):yield tree
    elif tree is None:return
    elif isinstance(tree,(list,tuple)):
        for subtree in tree:
            for node in get_leaf(subtree):yield node
    elif isinstance(tree,dict):
        for name,subtree in tree.items():
            for node in get_leaf(subtree):yield node
    else:raise TypeError(type(tree))
def get_stem(tree,on_path=False):
    if isinstance(tree,str):yield tree
    elif tree is None:return
    elif isinstance(tree,(list,tuple)):
        if not on_path:return
        for stem in get_stem(tree):yield stem
    elif isinstance(tree,dict):
        for link,subtree in tree.items():
            for stem in get_stem(link,on_path=True):yield stem
            if isinstance(subtree,str):continue
            for stem in get_stem(subtree):yield stem
    else:raise TypeError(type(tree))
class StateTree:
    @property
    def cur(self):return getattr(self.dfa.cur.state,self.name)
    def get_next(self,name):return getattr(self.dfa.next.state,name)
    def _complete_state_compute(self,tree,expr):
        if isinstance(tree,str):
            self.get_next(tree).condition|=expr
        elif isinstance(tree,dict):
            conditions = 0
            for cond,subtree in tree.items():
                if cond is None:continue
                next = self._compute_condition(cond)
                conditions |= next
                self._complete_state_compute(subtree,expr&next)
            if None in tree:
                self._complete_state_compute(tree[None],expr&~conditions)
        elif isinstance(tree,(tuple,list)):
            for subtree in tree:self._complete_state_compute(subtree,expr)
        else:raise TypeError(type(tree))
    def _compute_condition(self,cond):
        if isinstance(cond,str):return getattr(self.dfa.token,cond)
        if not isinstance(cond,tuple):raise TypeError()
        expr = 1
        for c in cond:expr&=getattr(self.dfa.token,c)
        return expr
    def complete(self,**kwargs):
        self._complete_state_compute(self.tree,self.cur)
    def __init__(self,dfa,name,tree,**kwargs):
        self.dfa  = dfa
        self.name = name
        self.tree = tree
        self.tokens = set(name for name in get_stem(tree))
        self.targets = set(name for name in get_leaf(tree))
class DFA(VStruct):
    '''
    Tooling DFA definition
    input:
    graph = {
    'start':
        |--str       :name of initail state
        +--not passed:DFA defined without an initail state
    'sequential':
        |--dict      :The state named as a key will be encoded with the value
        |--iterable  :The state encoded with i is named as the i-th name occured
        +--not passed:all states occured if there is an initail state
    'events':A list of cared events(signals)
    (other):states in DFA
    }
    waiting operates:
        1.fill expected token
        2.pass reset signal if any sequential
    '''
    def _prepare_sequetial_encode(self,sequential):
        self.sequential = [name for name in sequential]
        self.maxid = len(self.sequential)-1
        self.encode = {}
        for i in range(len(self.sequential)):
            self.encode[sequential[i]] = i
    def prepare_sequential(self):
        if 'sequential' in self.graph:
            sequential = self.graph['sequential']
            if isinstance(sequential,dict):
                self.maxid = max(index for name,index in sequential.items())
                self.sequential = [None]*len(sequential)
                self.encode = {}
                for name,code in sequential.items():
                    self.encode[name] = code
                    prev = self.sequential[code]
                    if not prev is None:
                        raise ValueError('Can not be encoded with "%s". State "%s" conflicts with previos state "%s".'%(code,name,prev))
                    self.sequential[code] = name
            else:self._prepare_sequetial_encode(sequential)
            del self.graph['sequential']
        else:self.sequential = None
        self.width = self.maxid if self.maxid<2 else int(1+math.log(self.maxid+0.5)/math.log(2))
    def prepare_start(self):
        if 'start' in self.graph:
            self.closed_loop = True
            self.start = self.graph['start']
            if isinstance(self.start,str):
                del self.graph['start']
            else:self.start = 'start'
            if self.start not in self.graph:
                raise NameError('Initial state "%s" is not defined.'%start)
        else:self.start  = None
    def prepare_events(self):
        if 'events' in self.graph:
            self.events = self.graph['events'].copy()
            del self.graph['events']
        else:self.events = None
    def __init__(self,graph,enableNFA=False,unreachable='error',escaped='normal',delay_errors=False,**kwargs):
        VStruct.__init__(self,**kwargs)
        self._origin_graph = graph
        self.enableNFA = enableNFA
        self.graph = graph.copy()
        for attrname in ['sequential','events','start']:getattr(self,'prepare_'+attrname)()
        if self.sequential is None:self._prepare_sequetial_encode(self.graph)
        if len(self.graph)==0:raise ValueError('No state defined.')
        self.trees = dict((name,StateTree(self,name,tree,**kwargs)) for name,tree in self.graph.items())
        self.states = set(name for name in self.trees)
        if self.events is None:self.events = self.states
        self.error = 0
        states = set()
        self.tokens = set()
        for name,tree in self.trees.items():
            states|=tree.targets
            self.tokens|=tree.tokens
        unreachable_states = self.states - states
        undeclare_events = self.events - states
        if len(unreachable_states)>0:
            if unreachable == 'error':
                print('Detected unreachable states in automaton:')
                print(','.join([name for name in unreachable_states]))
                self.error+=1
        if isinstance(escaped,str) and escaped == 'normal':pass
        else:
            escaped_states = states - self.states
            if isinstance(escaped,set):escaped_states-=escaped
            if len(escaped_states)>0 and (isinstance(escaped,set) or escaped == 'error'):
                print('Detected escaped states in automaton:')
                print(','.join([name for name in escaped_states]))
                self.error+=1
        self.states = states
        if self.error>0:
            raise ValueError('Totally %d errors detected in automaton design graph.')
        self.cur = VStruct()
        self.next = VStruct()
        self.token = VStruct()
        self.inter = VStruct()
    def _complete_state_declare(self,reset=None,cur=None,next=None,**kwargs):
        if not reset is None:self.reset = reset
        elif not self.start is None and not hasattr(self,'reset'):raise NameError('Expecting reset signal')
        if next is None:self.next.state = Wire(self.width) if self.width>0 else VStruct()
        else:self.next.state = next
        if not cur is None:self.cur.state = cur
        elif self.start is None:self.cur.state = Wire(self.width) if self.width>0 else VStruct()
        else:self.cur.state = Reg(self.width) if self.width>0 else VStruct()
        for name,code in self.encode.items():
            branch = Wire(self.cur.state.equal_to(code) if self.width>0 else 1)
            setattr(self.cur.state,name,branch)
        encode = 0
        for name,code in self.encode.items():
            target = Wire()
            setattr(self.next.state,name,target)
            target.condition = 0 if self.width>0 else 1
            encode|=Hexadecimal(code,width=self.width).validif(target)
        if self.width>0:self.next.state[:] = encode
        for name in self.states:
            if name in self.encode:continue
            branch = Wire()
            setattr(self.inter,name,branch)
            setattr(self.cur.state,name,branch)
            setattr(self.next.state,name,branch)
            branch.condition = 0
        
    def _complete_token_declare(self,token=None,**kwargs):
        if isinstance(token,str) and token == 'input':
            for name in self.tokens:
                if hasattr(self.token,name):continue
                setattr(self.token,name,Wire(io='input'))
        else:
            if isinstance(token,VStruct):self.token[:] = token
            missing = []
            for name in self.tokens:
                if hasattr(self.token,name):continue
                missing.append(name)
            if len(missing)>0:
                print('Input tokens are expected before generate:')
                print(','.join(name for name in missing))
                raise NameError('Expected names are not found.')
    def _complete_state_compute(self,active=None,**kwargs):
        for name,tree in self.trees.items():
            tree.complete(**kwargs)
        for name in self.states:
            target = getattr(self.next.state,name)
            target[:] = target.condition
        if not self.start is None:
            init = When(self.reset)[self.encode[self.start]]
            if active is None:next = init.Otherwise[self.next.state]
            else:next = init.When(active(event))[self.next.state]
            self.cur.state[:] = next
    def complete(self,**kwargs):
        self._complete_state_declare(**kwargs)
        self._complete_token_declare(**kwargs)
        self._complete_state_compute(**kwargs)
class NFA(VStruct):
    '''
    A array of DFA where they can use eachother's states as tokens with name "DFA.State"
    '''
    def __init__(self,graphs,enableNFA=True,**kwargs):
        VStruct.__init__(self,**kwargs)
        self._origin_graphs = graphs
        self.dfas = {}
        for name,graph in graphs.items():
            dfa = DFA(graph,start=starts.get(name,start),enableNFA=enableNFA,**kwargs)
            self.dfas[name] = dfa
            if hasattr(self,name):raise NameError('Name "%s" conflicts with previous "%s" object.'%type(getattr(self,name)))
            else:setattr(self,name,dfa)
    def complete(self,**kwargs):
        for name,dfa in self.dfas:
            dfa._complete_state_declare(**kwargs)
        for aname1,dfa1 in self.dfas.items():
            for aname2,dfa2 in self.dfas.items():
                if aname1 <= aname2:continue
                for sname1 in dfa1.states:
                    tname2 = '%s.%s'%(dfa1.name,sname1)
                    setattr(dfa2.token,tname2,getattr(dfa1.cur.state,sname1))
                for sname2 in dfa2.states:
                    tname1 = '%s.%s'%(dfa2.name,sname2)
                    setattr(dfa1.token,tname1,getattr(dfa2.cur.state,sname2))
        for name,dfa in self.dfas:
            dfa._complete_token_declare(**kwargs)
            dfa._complete_state_compute(**kwargs)