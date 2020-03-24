from pyvmodule import *
def simple_dpblkram(width,index,count=1,reset=False):
    ports = [
        'clka.i',
        'ena.i'+str(count),
        'wea.i'+str(count),
        'addra.i'+str(index),
        'dina.i'+str(width),
        'clkb.i',
        'enb.i',
        'addrb.i'+str(index),
        'doutb.or'+str(width)]
    ports+= ['rstb.o','rsta_busy.o','rstb_busy.o'] if reset else []
    class blockram(VModule[ports]):
        ip_only = True
        name_parts = ['simple','dp']
        name_parts+= ['reset'] if reset else []
        name_parts+= ['block','ram',str(width),str(index)]
        name_parts+= [str(count)] if count>1 else []
        name = '_'.join(name_parts)
    return blockram
def spblkram(width,index,count=1,reset=False):
    ports = [
        'clka.i',
        'ena.i',
        'wea.i'+str(count),
        'addra.i'+str(index),
        'douta.or'+str(width),
        'dina.i'+str(width)]
    ports+= ['rsta.o','rsta_busy.o'] if reset else []
    class blockram(VModule[ports]):
        ip_only = True
        name_parts = ['sp']
        name_parts+= ['reset'] if reset else []
        name_parts+= ['block','ram',str(width),str(index)]
        name_parts+= [str(count)] if count>1 else []
        name = '_'.join(name_parts)
    return blockram