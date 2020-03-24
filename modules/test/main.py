import sys
import os
vmodule_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../..')
cur_path =  set(sys.path)
if vmodule_dir not in cur_path:
    sys.path.insert(0,vmodule_dir)
from pyvmodule.tools.automata import *
from pyvmodule.develope import *
from pyvmodule.naming import NamingNode,NamingRoot
if __name__ == '__main__':
    graph = {
            'sequential':{
                'idle'        :0,'process'     :1,
                'line_holdon' :2,'hit_operate' :3,  
                'line_queuing':4,'line_waiting':5,
                'word_queuing':6,'word_waiting':7,
                'word_syncing':8,'line_syncing':9},
            'events':{
                'line_req'    ,'word_req'    ,
                'addr_ok'     ,'data_ok'     ,
                'capture'     ,'holdon'      ,
                'refill'      ,'lookup'      ,
                'cache_hit'   ,'cache_miss'  ,
                'process_cache','operate_ok' ,
                'bus_end'     ,'reusable'    ,
                'read'        ,'reuse'       ,
                'imm_operate' ,'hit_operate'},
            'start':'idle',
            'idle'          : {None:'free_finish'},
            
            'free_finish'   :({'operate':'go_operate',None:'all_addr_ok'   },{None:'operate_ok'}),
            'word_finish'   :({'operate':'go_operate',None:'new_addr_ok'   },{None:'operate_ok'}),
            'busy_finish'   : {'operate':'idle'      ,None:'conflict_check'},
            'conflict_check': {'again':'old_addr_ok' ,None:'idle'          },
            
            'go_operate' : {'op_hit': 'pre_hit_op',None: 'imm_operate'},
            'imm_operate': {None : 'idle'          },
            'pre_hit_op' : {None :('hit_operate','read','lookup')},
            'hit_operate': {None:'idle'},
            
            'all_addr_ok':({'req'   : 'reuse_check',None: 'idle'       },{None:'addr_ok'}),
            'old_addr_ok':({'req'   : 'reuse'      ,None: 'idle'       },{None:'addr_ok'}),
            'new_addr_ok':({'req'   : 'read_cache' ,None: 'idle'       },{None:'addr_ok'}),
            'reuse_check':({'again' : 'reuse'      ,None: 'read_cache' }),
            
            
            'addr_ok'    : {'req': 'lookup'         },
            'read_cache' : {None :('process','read')},
            'reuse'      : {None : 'line_holdon'    },
            'line_holdon':({None : 'free_finish'},{None:('data_ok'          ,'holdon'                     )}),
            
            'process'       : {'stop':'idle',None:'process_any'},
            'process_any'   : {None:'process_req'},
            'process_req'   : {'exception':'line_answer',None:'process_normal'},
            'process_normal': {'cache':'process_cache',None:'word_req'},
            'process_cache' : {'hit':'cache_hit',None:'cache_miss'},
            'cache_hit'     : {None:'line_answer'},
            'cache_miss'    : {None:'line_req'},
            
            'line_req'    : {'ready':'line_waiting',None:'line_queuing'},
            'line_queuing': {'stop' :'idle'        ,None:'line_req'    },
            'line_ack'    : {'valid':'line_refill' ,None:'line_waiting'},
            'line_waiting': {'stop' :'line_filter' ,None:'line_ack'    },
            'line_filter' : {'valid':'sync_refill' ,None:'line_syncing'},
            'line_syncing': {None:'line_filter'},
            'sync_refill' : {None:('idle','refill')},
            
            'word_req'    : {'ready':'word_waiting',None:'word_queuing'},
            'word_queuing': {'stop' :'idle'        ,None:'word_req'    },
            'word_ack'    : {'valid':'word_answer' ,None:'word_waiting'},
            'word_waiting': {'stop' :'word_filter' ,None:'word_ack'    },
            'word_filter' : {'valid':'all_addr_ok' ,None:'word_syncing'},
            'word_syncing': {None:'word_filter'},
            
            'word_answer'   :({None:'word_finish'},{None:('data_ok','capture','bus_end'                    )}),
            'line_answer'   :({None:'free_finish'},{None:('data_ok','capture'          ,'reusable'         )}),
            'line_refill'   :({None:'busy_finish'},{None:('data_ok','capture','bus_end','reusable','refill')})}
    dfa = DFA(graph)
    class Controller(VModule):
        clock = Wire(io='input')
        reset = Wire(io='input')
        core = dfa
        core.complete(reset=reset,token='input')
    print(str(Controller))