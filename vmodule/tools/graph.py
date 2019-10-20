from vmodule import *
try:
    import pygraphviz as pgv
    def plot_hierachy(module,name='out'):
        def get_hierachy(g,module,ploted):
            cls = type(module)
            for key in cls.mydict:
                obj = cls.mydict[key]
                if isinstance(obj,VModule):
                    obj_cls = type(obj)
                    edge = (cls.name,type(obj).name)
                    g.add_edge(edge)
                    get_hierachy(g,obj,ploted)
        g = pgv.AGraph(name=name)
        g.add_node(type(module).name)
        get_hierachy(g,module,{})
        g.layout('dot')
        g.draw(name+'.png')
except ImportError as e:
    print(e)
    def plot_hierachy(module,name='out'):
        return
