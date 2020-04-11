from .memorization import memorized
from .utility import clog2
@memorized
def gray_code(x):
    assert x>=0
    if x<=1:return x
    n = clog2(x)
    if x == (1<<n)-1:return 1<<(n-1)
    elif x == (1<<n):return 3<<(n-1)
    else:pass
    return 1<<(n-1) ^ gray_code((1<<n)-1-x)
@memorized
def gray_index(x):
    assert x>=0
    if x<=1:return x
    n = clog2(x)
    if x == 1<<n:return (1<<(n+1))-1
    elif x== 3<<(n-2):return 1<<(n-1)
    else:pass
    return (1<<n)-1-gray_index(1<<(n-1) ^ x)
if __name__ == '__main__':
    for i in range(16):
        if gray_code(gray_index(i)) != i:
            for j in range(16):
                print(j,gray_code(j),gray_index(gray_code(j)))
            raise NotImplementedError('Need Debug')
