
def gen_xml(vs,hist=None):
    if hist==None:
        hist = []
    lines = []
    lines.append('<vstruct name="'+str(vs._name)+'">')
    for key,val in vs.__dict__.items():
        if key[0]=='_':
            continue
        for other in hist:
            if other is val:
                print(lines)
                raise RuntimeError(key)
        if isinstance(val,(VStruct,Wire)):
            hist.append(val)
            if isinstance(val,Wire):
                lines.append('<'+str(val.typename)+' name="'+str(val)+'" io='+str(val.io)+'/>')
            else:
                lines.append(gen_xml(val,hist=hist))
    lines.append('</ vstruct>')
    return '\n'.join(lines)