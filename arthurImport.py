
import ast
import lark
import black
from pathlib import Path
from lark import Lark, Transformer, Visitor, v_args
from lark.indenter import Indenter
from lark.visitors import Interpreter
from dataclasses import dataclass
from pprint import pprint
from typing import Any, Optional, Union
from types import FunctionType
from itertools import chain


#https://github.com/lark-parser/lark/blob/master/docs/json_tutorial.md
#https://github.com/lark-parser/lark
#https://github.com/openscad/openscad/wiki/CSG-File-Format

class CsgModule(ast.Call):
    """
    Convenient marker.
    Really a module is just a function call with hidden "__children__" argument.
    """
    pass

class CsgTerminalTransformer(Transformer):
    """Simple transformer to handle some constants."""
    def SIGNED_INT(self, token: lark.lexer.Token):
        return token.update(value=int(token))
    def SIGNED_FLOAT(self, token: lark.lexer.Token):
        return token.update(value=float(token))
    def TRUE(self, token: lark.lexer.Token):
        return token.update(value=True)
    def FALSE(self, token: lark.lexer.Token):
        return token.update(value=False)
    def UNDEF(self, token: lark.lexer.Token):
        return token.update(value=None)


def empty_ast_args(splat):
    """Helper function for empty ast.arguments"""
    return ast.arguments(
        posonlyargs=[],
        args=[],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[],
        **splat
    )

class CsgToPythonAst(CsgTerminalTransformer):
    """Convert A Csg Tree to Python ast"""
    def _ast_splat(self, token):
        return {
            "lineno": token.line,
            "col_offset": token.column,
            "end_lineno": token.end_line,
            "end_col_offset": token.end_column
        }
    def _to_constant(self, token: lark.lexer.Token):
        return ast.Constant(token.value, **self._ast_splat(token))
    def SIGNED_INT(self, token: lark.lexer.Token):
        return self._to_constant(super().SIGNED_INT(token))
    def SIGNED_FLOAT(self, token: lark.lexer.Token):
        return self._to_constant(super().SIGNED_FLOAT(token))
    def TRUE(self, token: lark.lexer.Token):
        return self._to_constant(super().TRUE(token))
    def FALSE(self, token: lark.lexer.Token):
        return self._to_constant(super().FALSE(token))
    def UNDEF(self, token: lark.lexer.Token):
        return self._to_constant(super().UNDEF(token))
    def NAME(self, token: lark.lexer.Token):
        """Python's AST may handle $ in names, but the generated code is not valid. """
        return token.update(value=token.value.replace('$', 'DOLLAR_'))
    @v_args(tree=True)
    def array(self, tree: lark.tree.Tree):
        return ast.List(elts=tree.children, ctx=ast.Load(), **self._ast_splat(tree.data))
    @v_args(tree=True)
    def named_argument(self, tree: lark.tree.Tree):
        assert len(tree.children) == 2
        return ast.keyword(arg=tree.children[0].value, value=tree.children[1], **self._ast_splat(tree.data))
    def positional_argument(self, children: list):
        assert len(children) == 1
        return children[0]
    def arguments(self, children: list) -> tuple[list, list[ast.keyword]]:
        """
        Tuple of args, kwargs

        Deliberately not bothering with the following cases:
        * args after kwargs
        * multiple kwargs which are the same
        """
        return list(filter(lambda i: not isinstance(i, ast.keyword), children)), \
               list(filter(lambda i: isinstance(i, ast.keyword), children))
    @v_args(tree=True)
    def scope(self, tree: lark.tree.Tree) -> tuple[ast.FunctionDef, ast.keyword]:
        """
        Python doesn't have the concept of anonymous scopes or multi-line lambdas.
        Instead use a function definition and a keyword argument to call said definition.
        """
        splat = self._ast_splat(tree.data)
        calls = list(chain.from_iterable(tree.children))
        scope_id = f"__children_{abs(hash(str(calls)))}"
        children = ast.FunctionDef(name=scope_id, body=calls,
            args=empty_ast_args(splat), decorator_list=[], **splat)
        keyword = ast.keyword(arg='__children', value=ast.Name(id=scope_id, ctx=ast.Load(), **splat), **splat)
        return children, keyword
    @v_args(tree=True)
    def object(self, tree: lark.tree.Tree) -> tuple[ast.Expr]:
        assert len(tree.children) == 2
        splat = self._ast_splat(tree.data)
        name = ast.Name(id=tree.children[0].value, ctx=ast.Load(), **splat)
        args, kwargs = tree.children[1]
        return tuple([ast.Expr(value=ast.Call(func=name, args=args, keywords=kwargs, **splat), **splat)])
    @v_args(tree=True)
    def module(self, tree: lark.tree.Tree) -> tuple[ast.FunctionDef, ast.Expr]:
        """
        A module is just a function call where one variable is passed in differently.
        The scope that comes after the function "{...}" can be thought of as a multi-line anonymous function/lambda
        that is accessed by the "children();" call.
        """
        assert len(tree.children) == 3
        splat = self._ast_splat(tree.data)
        name = ast.Name(id=tree.children[0].value, ctx=ast.Load(), **splat)
        args, kwargs = tree.children[1]
        children, scope_keyword = tree.children[2]
        return children, \
            ast.Expr(value=ast.Call(func=name, args=args, keywords=kwargs + [scope_keyword], **splat), **splat)
    @v_args(tree=True)
    def start(self, tree: lark.tree.Tree):
        calls = list(chain.from_iterable(tree.children))
        return ast.Module(body=calls, type_ignores=[], **self._ast_splat(tree.data))

csg_python_ast = CsgToPythonAst().transform(parsed)
debug_view = ast.dump(csg_python_ast, indent=1, include_attributes=True)
raw_csg_python = ast.unparse(csg_python_ast)
formatted_csg_python = black.format_str(raw_csg_python, mode=black.Mode())

out_path.write_text(debug_view)
out_path.write_text(raw_csg_python)
out_path.write_text(formatted_csg_python)

node = csg_python_ast.body
for i in range(9):
    node = node.keywords[0].value.elts[0]
n = ast.parse('print()', mode='eval')
co = compile(ast.Expression(node), '-', mode='eval')

co = compile(csg_python_ast, '-', mode='exec')
fn = FunctionType(code=co, globals={})
fn()

class SourceOffsetVisitor(ast.NodeVisitor):
    def generic_visit(self, node):
        super().generic_visit(node)
        if not isinstance(node, (ast.expr, ast.stmt, ast.pattern)):
            return
        lines.add(node.lineno)
        end_lines.add(node.end_lineno)
        columns.add(node.col_offset)
        end_columns.add(node.end_col_offset)

class CsgWriter(Interpreter):
    """Transforms the rest of the tree into a CSG File"""
    def __init__(self, indent : str = "  "):
        self.indent = indent
        self.level = 0
    def start(self, tree: lark.tree.Tree):
        assert isinstance(tree, lark.tree.Tree)
        return "\n".join([self.visit(child) for child in tree.children])
    def module(self, tree: lark.tree.Tree):
        assert isinstance(tree, lark.tree.Tree)
        items = tree.children
        return f"{items[0]}({items[1]}) {self.visit(items[2])}"
    def scope(self, tree: lark.tree.Tree):
        assert isinstance(tree, lark.tree.Tree)
        self.level += 1
        prepend = self.indent * self.level
        out = "{\n"
        for item in tree.children:
            if isinstance(item, lark.tree.Tree):
                out += prepend + self.visit(item) + "\n"
                continue
            out += prepend + item + "\n"
        self.level -= 1
        #out = out.rstrip() # Prevent duplicate newlines
        out += self.indent * self.level + "}"
        return out

class CsgTransformWriter(Transformer):
    """Transforms most of the tree to a CSG file."""
    def SIGNED_INT(self, token: lark.lexer.Token):
        return int(token)
    def SIGNED_FLOAT(self, token: lark.lexer.Token):
        return float(token)
    def TRUE(self, token: lark.lexer.Token):
        return "true"
    def FALSE(self, token: lark.lexer.Token):
        return "false"
    def UNDEF(self, token: lark.lexer.Token):
        return "undef"
    def array(self, items: list):
        return list(items)
    def named_argument(self, items: list):
        return f"{items[0]} = {items[1]}"
    def positional_argument(self, items: list):
        return str(items[0])
    def arguments(self, items: list):
        return ", ".join(items)
    def object(self, items: list):
        assert len(items) == 2
        return f"{items[0]}({items[1]});"

larkfile_path = Path("parser.lark")
file_path = Path('test1.csg')
out_path = Path('out.txt')


def run_lark():
    parser = Lark(larkfile_path.read_text(), parser='lalr', transformer=CsgTerminalTransformer(), strict=True)
    parsed = parser.parse(file_path.read_text())
    out_path.write_text(parsed.pretty(' '))
    #pprint(t)

def transform():
    t = CsgTransformer().transform(parsed)
    out_path.write_text(t.pretty(' '))

def write():
    partial = CsgTransformWriter().transform(parsed)
    writer = CsgWriter("\t")
    final = writer.visit(partial)
    out_path.write_text(final)
