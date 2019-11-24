
def bitwise_count_one(expr):
    x = int(expr)
    n = len(expr)
    retval = 0
    for i in range(n):
        if (x&(1<<i))!=0:
            retval+=1
    return retval
def expr__neg(expr):
    n = len(rhs)
    rhs = int(rhs)
    rhs^=(1<<n)-1
    return (rhs+1)&((1<<n)-1)
def expr__sub(lhs,rhs):
    n = max(len(rhs),len(rhs))
    return (int(lhs)-int(rhs))&((1<<n)-1)
def expr__replicate(lhs,rhs):
    pattern = int(lhs)
    retval = pattern
    width = len(lhs)
    num = int(rhs)
    i = 2
    while i<num:
        retval |= retval<<(width*(i-1))
        i<<=1
    i>>=1
    retval |= retval<<(width*(num-i))
    return retval
actions = {
    '^':lambda lhs,rhs:int(lhs)^int(rhs),
    '&':lambda lhs,rhs:int(lhs)&int(rhs),
    '|':lambda lhs,rhs:int(lhs)|int(rhs),
    '&&':lambda lhs,rhs:int(lhs)&int(rhs),
    '||':lambda lhs,rhs:int(lhs)|int(rhs),
    '+':lambda lhs,rhs:(int(lhs)+int(rhs))&((1<<len(lhs))-1),
    '-':lambda lhs,rhs:expr__sub(lhs,rhs),
    '==':lambda lhs,rhs:1 if int(lhs)==int(rhs) else 0,
    '!=':lambda lhs,rhs:1 if int(lhs)!=int(rhs) else 0,
    '<=':lambda lhs,rhs:1 if int(lhs)<=int(rhs) else 0,
    '<' :lambda lhs,rhs:1 if int(lhs)< int(rhs) else 0,
    '>=':lambda lhs,rhs:1 if int(lhs)>=int(rhs) else 0,
    '>' :lambda lhs,rhs:1 if int(lhs)> int(rhs) else 0,
    '<<':lambda lhs,rhs:(int(lhs)<<rhs)&((1<<len(lhs))-1),
    '>>':lambda lhs,rhs:(int(lhs)>>rhs)&((1<<len(lhs))-1),
    '~' :lambda rhs:int(rhs)^((1<<len(rhs))-1),
    '!' :lambda rhs:int(rhs)^((1<<len(rhs))-1),
    ' ' :lambda rhs:int(rhs),
    ' -':lambda rhs:expr__neg(rhs),
    ' |':lambda rhs:1 if int(rhs)!=0 else 0,
    ' &':lambda rhs:1 if int(rhs)==(1<<len(rhs))-1 else 0,
    ' ^':lambda rhs:bitwise_count_one(rhs)%2,
    '?:':lambda lhs,rhs,cond:int(lhs) if int(cond)!=0 else int(rhs),
    '{{}}':lambda lhs,rhs:expr__replicate(lhs,rhs)}