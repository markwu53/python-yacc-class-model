from collections import namedtuple
import abc

R = namedtuple("R", "s p r")
T = namedtuple("T", "t v")

def tokenize_char_source(char_source): return [T("c", ch) for ch in char_source]

class Parser(abc.ABC):

    def __init__(self, tokens):
        self.tokens = tokens
        self.base_init()
        self.pre()
    @abc.abstractmethod
    def pre(self):
        pass
    @abc.abstractmethod
    def parse(self):
        pass

    def S(self, *fs):
        def fp(p):
            y = []
            for i,f in enumerate(fs):
                x = f(p if i == 0 else x.p)
                if not x.s:
                    return R(False, p, [])
                y.append(x.r)
            return R(True, x.p, y)
        return fp

    def P(self, *fs):
        def fp(p):
            for f in fs:
                x = f(p)
                if x.s:
                    return x
            return R(False, p, [])
        return fp

    #def M(f): return S(f, O(lambda p: M(f)(p)))
    def M(self, f):
        def fp(p):
            x = f(p)
            y = []
            if not x.s:
                return x
            while x.s:
                y.append(x.r)
                x = f(x.p)
            return R(True, x.p, y)
        return fp

    def nothing(self, p): return R(True, p, [])
    def O(self, f): return self.P(f, self.nothing)
    def Z(self, f): return self.O(self.M(f))
    def N(self, f, g): return lambda p: (lambda x: R(False, p, []) if x.s else g(p))(f(p))
    def post(self, pp, f): return lambda p: (lambda x: pp(x, p) if x.s else x)(f(p))
    def postr(self, pp, f): return self.post(lambda x, p: R(x.s, x.p, pp(x.r)), f)
    def flatten(self, r): return [y for x in r for y in self.flatten(x)] if isinstance(r, list) else [r]
    def check_item(self, good, f): return self.post(lambda x, p: x if good(x.r[0]) else R(False, p, []), f)
    def get_token(self, p): return R(False, p, []) if p == len(self.tokens) else R(True, p + 1, [self.tokens[p]])
    def check_token(self, good): return self.check_item(good, self.get_token)
    def make_token(self, t): return lambda r: [T(t, "".join([e.v for e in self.flatten(r)]))]
    def N1(self, f): return self.N(f, self.get_token)
    def CC(self, pr): return self.check_token(lambda tc: pr(tc.v))
    def ttype(self, type): return self.check_token(lambda t: t.t == type)
    def s(self, a): return self.check_token(lambda tc: a==tc.v)

    def base_init(self):
        self.any = self.get_token
        self.is_alpha = self.CC(str.isalpha)
        self.is_digit = self.CC(str.isdigit)
        self.is_space = self.CC(str.isspace)
        self.line_comment_end = self.P(self.S(self.s("\r"),self.s("\n")),self.S(self.s("\n"),self.s("\r")),self.s("\r"),self.s("\n"))
        self.line_comment_char = self.N1(self.P(self.s("\r"), self.s("\n")))
        self.block_comment_char = self.N1(self.S(self.s("*"),self.s("/")))
        self.quote = self.s("'")
        self.dquote = self.s('"')
        self.make_token_identifier = self.make_token("identifier")
        self.make_token_space = self.make_token("space")
        self.make_token_line_comment = self.make_token("line_comment")
        self.make_token_block_comment = self.make_token("block_comment")
        self.make_token_symbol = self.make_token("symbol")

class LexParser(Parser):

    def lex(self, p): return self.Z(self.one_token)(p)
    def one_token(self, p): return self.P(self.postr(self.make_token_identifier,self.identifier),self.postr(self.make_token_space,self.space),self.postr(self.make_token_ysymbol,self.ysymbol),self.postr(self.make_token_ykeyword,self.ykeyword),self.postr(self.make_token_line_comment,self.line_comment),self.postr(self.make_token_block_comment,self.block_comment),self.postr(self.make_token_symbol,self.symbol))(p)
    def identifier(self, p): return self.S(self.identifier_first_char,self.Z(self.identifier_next_char))(p)
    def identifier_first_char(self, p): return self.P(self.is_alpha,self.s("_"))(p)
    def identifier_next_char(self, p): return self.P(self.identifier_first_char,self.is_digit)(p)
    def space(self, p): return self.M(self.is_space)(p)
    def ysymbol(self, p): return self.S(self.quote,self.any,self.quote)(p)
    def ykeyword(self, p): return self.S(self.dquote,self.identifier,self.dquote)(p)
    def symbol(self, p): return self.any(p)
    def line_comment(self, p): return self.S(self.s("/"),self.s("/"),self.Z(self.line_comment_char),self.line_comment_end)(p)
    def block_comment(self, p): return self.S(self.s("/"),self.s("*"),self.Z(self.block_comment_char),self.s("*"),self.s("/"))(p)

    def pre(self):
        self.make_token_ysymbol = self.make_token("ysymbol")
        self.make_token_ykeyword = self.make_token("ykeyword")

    def parse(self):
        self.remove_types = ["space", "line_comment", "block_comment"]
        tokens = [e for e in self.flatten(self.lex(0).r) if e.t not in self.remove_types]
        return tokens

class YaccParser(Parser):

    def y_grammar(self, p): return self.M(self.y_entry)(p)
    def y_entry(self, p): return self.postr(self.pdef,self.S(self.y_term,self.s("="),self.y_entry_def,self.s(";")))(p)
    def y_entry_def(self, p): return self.postr(self.pcombine,self.S(self.y_sequence,self.y_or_sequences))(p)
    def y_or_sequences(self, p): return self.postr(self.pcollect,self.Z(self.y_or_sequence))(p)
    def y_or_sequence(self, p): return self.postr(self.pskip,self.S(self.s("|"),self.y_sequence))(p)
    def y_sequence(self, p): return self.postr(self.ppost,self.S(self.y_seq_objects,self.O(self.y_post_processing)))(p)
    def y_post_processing(self, p): return self.postr(self.pskip,self.S(self.p_post_op,self.y_processing))(p)
    def p_post_op(self, p): return self.S(self.s("-"),self.s(">"))(p)
    def y_seq_objects(self, p): return self.postr(self.pseq,self.M(self.y_seq_object))(p)
    def y_seq_object(self, p): return self.P(self.postr(self.pzero,self.S(self.y_term,self.s("*"))),self.postr(self.pmore,self.S(self.y_term,self.s("+"))),self.postr(self.poptional,self.S(self.y_term,self.s("?"))),self.y_term,self.y_symbol,self.postr(self.poptional,self.S(self.y_keyword,self.s("?"))),self.y_keyword)(p)
    def y_term(self, p): return self.y_identifier(p)
    def y_processing(self, p): return self.y_identifier(p)

    def pre(self):
        self.defined_terms = set()
 
        self.p1 = lambda r: ["self.{}".format(r[0].v)]
        self.pzero = lambda r: ["self.Z({})".format(self.flatten(r)[0])]
        self.pmore = lambda r: ["self.M({})".format(self.flatten(r)[0])]
        self.poptional = lambda r: ["self.O({})".format(self.flatten(r)[0])]
        self.pskip = lambda r: [r[1]]
        self.pcollect = lambda r: self.flatten(r)

        self.y_symbol = self.postr(self.ps1, self.ttype("ysymbol"))
        self.y_keyword = self.postr(self.ps2, self.ttype("ykeyword"))
        self.y_identifier = self.postr(self.p1, self.ttype("identifier"))

    def ps1(self, r):
        ch = r[0].v[1:-1]
        ret = "self.s('{}')".format(ch) if ch == '"' else 'self.s("{}")'.format(ch)
        return [ret]

    def ps2(self, r):
        k = r[0].v[1:-1]
        ret = 'self.kword("{}")'.format(k)
        return [ret]

    def pseq(self, r):
        x = self.flatten(r)
        if len(x) == 1:
            ret = x[0]
        else:
            ret = "self.S({})".format(",".join(x))
        return [ret]

    def ppost(self, r):
        x = self.flatten(r)
        if len(x) == 2:
            ret = "self.postr({1},{0})".format(*x)
        else:
            ret = x[0]
        return [ret]

    def pcombine(self, r):
        x = self.flatten(r)
        if len(x) == 1:
            ret = x[0]
        else:
            ret = "self.P({})".format(",".join(x))
        return [ret]

    def pdef(self, r):
        r = self.flatten(r)
        self.defined_terms.add(r[0])
        x = "{1}({0}, p)".format(*r[0].split(r"."))
        ret = "    def {}: return {}(p)".format(x, r[2])
        return [ret]

    def parse(self):
        result = self.y_grammar(0)

        used_terms = {term for t,term in self.tokens if t == "identifier"}
        undefined_terms = sorted(list(used_terms - self.defined_terms))
        print("Undefined Terms:")
        for e in undefined_terms: print(e)
        print()

        return R(result.s, result.p, self.flatten(result.r))

def run():
    with open("pyacc.txt") as fd: char_source = fd.read()
    tokens = tokenize_char_source(char_source)

    lex_parser = LexParser(tokens)
    tokens = lex_parser.parse()
    #for e in tokens: print(e)
    #print()

    yacc_parser = YaccParser(tokens)
    result = yacc_parser.parse()
    print(result.s, result.p)
    for e in result.r: print(e)

if __name__ == "__main__":
    run()
