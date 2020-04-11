from .memorization import memorized
__all__ = ['Polynomial']
class PolynomialBase:
    def __or__(self,x):
        q = int(self)|int(x)
        return type(self)(q)
    def __and__(self,x):
        q = int(self)&int(x)
        return type(self)(q)
    def __ne__(self,x):
        if x==None:
            return False
        return int(self)!=int(x)
    def __xor__(self,x):
        q = self.q^int(x)
        retval = type(self)(q)
        return retval
    def __pow__(self,n):
        x = type(self)(self)
        y = type(self)(1)
        i = 0
        while n!=0:
            if (n&(1<<i))!=0:
                y = y*x
                n^= 1<<i
            i+=1
            x = x*x
        return type(self)(y)
    def __int__(self):
        return int(self.q)
    def __lshift__(self,n):
        x = int(self)
        for i in range(n):
            x<<=1
            if(x&(1<<self.deg)):
                x &=(1<<self.deg)-1
                x ^=self.seed
        return type(self)(x)
    def __rshift__(self,n):
        if self.seed&1 == 0:raise NotImplementedError()
        for i in range(n):
            if (x&1) == 1:
                x^=seed|(1<<deg)
            x>>=1
        return type(self)(x)
    def __mul__(self,x):
        x = int(x)
        i = 0
        y = 0
        while x!=0:
            if (x&(1<<i))!=0:
                y^= self.q<<i
                x^= 1<<i
            i+=1
        i = 0
        s = 1
        while y!=0:
            if (y&(1<<i))!=0:
                x^= s
                y^=(1<<i)
            i+=1
            s <<= 1
            if (s&(1<<self.deg))!=0:
                s^=1<<self.deg
                s^=self.seed
        return type(self)(x)
    def cast(self,x):
        if x<0:raise NotImplementedError()
        shift = 0
        mask  = 1<<self.deg
        while mask < x:
            if x&mask:
                x^= mask
                x^= self.seed<<shift
            shift += 1
            mask <<= 1
        return x
@memorized
def Polynomial(deg,seed):
    if (seed&(1<<deg))!=0:seed^=(1<<deg)
    if type(deg)!=int:raise TypeError(type(deg))
    def get_init(self,x):
        self.deg = deg
        self.seed= seed
        self.q = self.cast(int(x))
    class _Polynomial(PolynomialBase):
        __init__ = get_init
    return _Polynomial
