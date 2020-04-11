__all__ = ['align_mat','align_assign','join_mat','align_expr_area']
def join_mat(mat):return [''.join(line)  for line in mat]
def count_line_width(line,start=0,end=None):
    if end is None:end = len(line)
    width = 0
    for i in range(start,end):width += len(line[i])
    return width
def get_max_width(mat,col,start=0,end=None,word=None):
    if end is None:end = len(mat)
    max_width = max((len(mat[i][col]) if col<len(mat[i]) and mat[i][col] != word else -1) for i in range(start,end))
    return max_width
def mat_align_col(mat,col,start=0,end=None,word=None):
    if end is None:end = len(mat)
    max_width = get_max_width(mat,col,start,end,word)
    if max_width<0:return max_width
    myindent = ' '*max_width
    for i in range(start,end):
        if mat[i][col] != word:mat[i][col] = mat[i][col].ljust(max_width)
        else:mat[i].insert(col,myindent)
    return max_width
def align_mat(mat):
    if len(mat)<=0:return []
    for col in range(len(mat[0])):mat_align_col(mat,col)
    return mat
def assert_assign(mat,i):
    if mat[i][0] == 'assign ':
        if mat[i][2] == ' = ' or len(mat[i])>=7 and mat[i][7] == ' = ':
            return
    raise SyntaxError('Invalid generate result')
def align_assign(mat):
    top = 0
    while top<len(mat):
        bottom = top
        assert_assign(mat,top)
        tail = bottom
        while bottom+1<len(mat):
            while ';' not in mat[tail]:
                tail+=1
                assert tail<len(mat)
            if tail>bottom:
                break
            bottom+=1
            tail = bottom
            assert_assign(mat,bottom)
        if tail<bottom:tail = bottom
        align_assign_area(mat,top,bottom,tail)
        top = tail+1
    return mat
padding_set = {'!','~'} 
pattern_ignore = padding_set|{';'}
tranlate_set = {'':0,'{':3,',':3}
is_num = lambda letter:letter == "'" or letter.isdigit()
is_var = lambda letter:letter == "_" or letter.isalpha()
def seq_align_expr_area_record(mat,col,row):
    pattern = []
    for j in range(col,len(mat[row])):
        word = mat[row][j]
        if word in pattern_ignore:continue
        elif word in tranlate_set:pattern.append(tranlate_set[word])
        elif is_num(word[0]):pattern.append(1)
        elif is_var(word[0]):pattern.append(2)
        else:pattern.append(word)
    return pattern
def seq_align_expr_area_match(mat,col,row,prev):
    next = seq_align_expr_area_record(mat,col,row)
    if len(next)!=len(prev):return False
    for i in range(len(next)):
        if prev[i]!=next[i]:return False
    return True
def seq_align_expr_area_fit_padding(mat,col,top,cur):
    for i in range(top,cur):
        if col >= len(mat[i]):continue
        word = mat[i][col]
        if word in padding_set:
            myindent = ' '*len(word)
            for k in range(top,cur):
                if mat[k][col] not in padding_set:mat[k].insert(col,myindent)
            return True
    return False
def seq_align_expr_area_fit(mat,col,top,cur):
    while True:
        if col>=len(mat[top]):break
        if seq_align_expr_area_fit_padding(mat,col,top,cur):pass
        else:
            word = mat[top][col]
            if word in tranlate_set or is_num(word[0]) or is_var(word[0]):mat_align_col(mat,col,top,cur)
        col+=1
def align_expr_area(mat,col=0,top=0,tail=None):
    if tail is None:tail = len(mat)-1
    while top<=tail:
        pattern = seq_align_expr_area_record(mat,col,top)
        cur = top+1
        while cur<=tail and seq_align_expr_area_match(mat,col,cur,pattern):cur+=1
        seq_align_expr_area_fit(mat,col,top,cur)
        top = cur
def align_assign_area(mat,top,bottom,tail):
    col = 0
    while True:
        if align_assign_area_col(mat,top,bottom,tail,col):col+=1
        else:break
    align_expr_area(mat,col+1,top,tail)
    return mat
def align_assign_area_col(mat,top,bottom,tail,col):
    max_width = mat_align_col(mat,col,top,bottom+1,word=' = ')
    fail = max_width<0
    if fail:
        max_width = get_max_width(mat,col,top,bottom+1)
        for i in range(len(mat)):
            if col<len(mat[i]):
                if mat[i][col]==';':continue
                mat[i][col] = mat[i][col].rjust(max_width)
        return False
    else:
        myindent = ' '*max_width
        for i in range(bottom+1,tail+1):mat[i].insert(col,myindent)
        return True
if __name__ == '__main__':
    print('Test align.')
    def test(align,mat):
        return '\n'.join([''.join(line) for line in align(mat)])
    '''
    ...
    assign a1     = b1;
    assign a2     = b2;
    assign c [0 ] = d[0 ];
    assign c [1 ] = d[1 ];
    ...    
    assign c [10] = d[10];
    assign e      = f
                  | g
                  | h;
    '''
    mat1 = [
        ['input  ','wire',' ','[','9',':','0',']',' ','prev',','],
        ['output ','reg',' ','[','10',':','0',']',' ','index','']]
    seq1 = [
        ['assign ','index_dec','[','','','0',']',' = ','!','index','[','0',']',' && ','!','index','[','1',']',';'],
        ['assign ','index_dec','[','','','1',']',' = ','index','[','0',']',' && ','!','index','[','1',']',';'],
        ['assign ','index_dec','[','','','2',']',' = ','!','index','[','0',']',' && ','index','[','1',']',';'],
        ['assign ','index_dec','[','','','3',']',' = ','index','[','0',']',' && ','index','[','1',']',';']]
    seq2 = [
        ['assign ','a',' = ','bbb',' & ','c',';'],
        ['assign ','aa',' = ','bb',' & ','c',';'],
        ['assign ','aaa',' = ','b',' & ','c',';']]
    print(test(align_mat,mat1))
    print(test(align_assign,seq1))
