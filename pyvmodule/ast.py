from .language import verilog
langs = {'verilog':verilog}
class ASTNode:
    _expr_generate_funcs = verilog.expr_generate_funcs
    _cblk_generate_funcs = verilog.cblk_generate_funcs
    _decl_generate  = verilog.decl_generate
    _inst_generate  = verilog.inst_generate
    _meta_generate  = verilog.meta_generate
    _language = 'verilog'
    @property
    def _decl_stmt(self):raise NotImplementedError('')
    @staticmethod
    def get_language():return ASTNode._language
    @staticmethod
    def set_language(language):
        if language not in langs:raise NotImplementedError('pyvmodule does not support language module "%s"',language)
        ASTNode._language = language
        lang_module = langs[language]
        ASTNode._expr_generate_funcs = lang_module.expr_generate_funcs
        ASTNode._cblk_generate_funcs = lang_module.cblk_generate_funcs
        ASTNode._decl_generate  = lang_module.decl_generate
        ASTNode._inst_generate  = lang_module.inst_generate
    _ASTNode_object_id = 0
    _expr_possible_typenames = {
        'wire'   ,'reg'    ,
        'const'  ,'~'      ,
        ' &'     ,' |'     ,
        ' ^'     ,' -'     ,
        '<<'     ,'>>'     ,
        '=='     ,'!='     ,
        '<'      ,'>'      ,
        '>='     ,'<='     ,
        '+'      ,'-'      ,
        '*'      ,
        '/'      ,'%'      ,
        '&'      ,'|'      ,
        '{}'     ,'{{}}'   ,
        '^'      ,'[]'     ,
        '?:'     ,'validif'}
    _expr_n_childs = {
        '~'      :1,
        ' &'     :1,' |'     :1,
        ' ^'     :1,' -'     :1,
        '<<'     :2,'>>'     :2,
        '=='     :2,'!='     :2,
        '<'      :2,'>'      :2,
        '>='     :2,'<='     :2,
        '+'      :0,'-'      :2,
        '*'      :2,
        '/'      :2,'%'      :2,
        '&'      :0,'|'      :0,
        '{}'     :0,'{{}}'   :1,
        '^'      :0,'[]'     :2,
        '?:'     :3,'validif':2}
    _index_possible_typenames = {
        'range'  ,
        '+:'     ,'-:'     }
    _controlblock_possible_typenames = {
        'always@','always#',
        'initial',
        'if'     ,'else'   }
    _controlblock_n_childs = {
        'always@':2,
        'always#':1,
        'initial':1,
        'if'     :3,
        'else'   :1}
    def __hash__(self):
        return str(self).__hash__()
    def _generate(self,*arg,**kwargs):raise NotImplementedError()
    def __str__(self):return '\n'.join([''.join(line) for line in self._generate()])
    def __eq__(self,other):
        if self is other:return True
        else:return str(self) == str(other)
