def binary(bin):
    val = 0
    for b in bin:
        if b in {'1','0'}:
            val<<= 1
        else:
            assert b=='-'
        if b=='1':
            val|= 1
        else:
            assert b=='0'
    return val