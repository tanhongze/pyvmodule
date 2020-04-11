def dpram(self,widths,count=1,depth=None,reset=False,ip_only=True):
    count = count if isinstance(widths,int) else len(widths)
    depth = self.index if depth==None else depth
    width = widths*count if isinstance(widths,int) else reduce(lambda a,b:a+b,widths)
    ports = [
        'clk.i',
        're.i',
        'raddr.i'+str(depth),
        'rdata.or'+str(width),
        'we.i'+str(count),
        'waddr.i'+str(depth),
        'wdata.i'+str(width)]
    class blockram(VModule[ports]):
        name_parts = ['dp']+(['reset'] if reset else [])+['block','ram',str(depth),str(width)]
        name_parts+= [str(count)]                   if count>1                             else []
        name_parts+= [str(area) for area in widths] if count>1 and isinstance(widths,list) else []
        name = '_'.join(name_parts)
        clock = clk
        if width==1:
            ram = Reg(width=1<<depth,pragmas={'ram_style':'blockram'})
            ram[waddr] = Always(clk)[When(we)[wdata]]
        else:
            ram = Reg(width=width,length=1<<depth,pragmas={'ram_style':'blockram'})
            cur = 0
            for i in range(count):
                next = cur + (widths if isinstance(widths,int) else widths[i])
                ram[addr][cur:next] = Always(clk)[When(we[i])[wdata[cur:next]]]
                cur = next
        rdata[:] = Always(clk)[When(re)[ram[raddr]]]
    
    blockram.ip_only = ip_only
    return blockram
def spram(self,widths,count=1,depth=None,ip_only=True):
    count = count if isinstance(widths,int) else len(widths)
    depth = self.index if depth==None else depth
    width = widths*count if isinstance(widths,int) else reduce(lambda a,b:a+b,widths)
    ports = [
        'clk.i',
        'en.i',
        'wen.i'+str(count),
        'addr.i'+str(depth),
        'wdata.i'+str(width),
        'rdata.or'+str(width)]
    class blockram(VModule[ports]):
        name = 'blockram_%d_%d_%d%s'%(depth,width,count,'' if isinstance(widths,int) else '_'.join(['']+widths))
        
        if width==1:
            ram = Reg(width=1<<depth,pragmas={'ram_style':'blockram'})
            ram[addr] = Always(clk)[When(en&wen)[wdata]]
        else:
            ram = Reg(width=width,length=1<<depth,pragmas={'ram_style':'blockram'})
            cur = 0
            for i in range(count):
                next = cur + (widths if isinstance(widths,int) else widths[i])
                ram[addr][cur:next] = Always(clk)[When(en&wen[i])[wdata[cur:next]]]
                cur = next
        rdata[:] = Always(clk)[When(en&~BitReduce('|',wen))[ram[addr]]]
    
    blockram.ip_only = ip_only
    return blockram