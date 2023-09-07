from syntax import WhileParser
import operator
from z3 import Int, ForAll, Implies, Not, And, Or, Solver, unsat, sat


OP = {'+': operator.add, '-': operator.sub,
      '*': operator.mul, '/': operator.floordiv,
      '!=': operator.ne, '>': operator.gt, '<': operator.lt,
      '<=': operator.le, '>=': operator.ge, '=': operator.eq}


def mk_env(pvars):
    return {v : Int(v) for v in pvars}

def upd(d, k, v):
    d = d.copy()
    d[k] = v
    return d

def vars_from_ast(ast):
    '''
    Returns a list of the variables in the given AST.
    '''
    match ast.root:
        case 'skip':
            return []
        case ':=':
            id = ast.subtrees[0].subtrees[0].root;
            vars = vars_from_ast(ast.subtrees[1])
            vars.append(id)
            return vars
        case 'if':
            vars = vars_from_ast(ast.subtrees[0])
            vars = vars + vars_from_ast(ast.subtrees[1])
            vars = vars + vars_from_ast(ast.subtrees[2])
            return vars
        case 'num':
            return []
        case 'id':
            return [ast.subtrees[0].root]
        case 'while':
            vars = vars_from_ast(ast.subtrees[0])
            vars = vars + vars_from_ast(ast.subtrees[1])
            return vars
        case 'assert':
            return vars_from_ast(ast.subtrees[0])
        case _:
            # OP case or ; case
            vars = vars_from_ast(ast.subtrees[0])
            vars = vars + vars_from_ast(ast.subtrees[1])
            return vars
                
def get_expr_value(ast, env):
    '''
    Returns the value of the expression represented by the AST
    in the given environment.
    '''
    match ast.root:
        case 'num':
            return ast.subtrees[0].root
        case 'id':
            return env[ast.subtrees[0].root]
        case _:
            left_side = get_expr_value(ast.subtrees[0], env)
            right_side = get_expr_value(ast.subtrees[1], env)
            return OP[ast.root](left_side, right_side)

def assign_wp(ast, Q):
    '''
    The weakest precondition for an assignment statement.
    '''
    id = ast.subtrees[0].subtrees[0].root
    right_side = ast.subtrees[1]
    return lambda env: Q(upd(env, id, get_expr_value(right_side, env)))

def psicuda_wp(ast, vars, Q, linv):
    '''
    The weakest precondition for a sequence of statements. (; case)
    '''
    left_side = ast.subtrees[0]
    right_side = ast.subtrees[1]
    return globals()['get_weakest_precondition'](left_side, vars, globals()['get_weakest_precondition'](right_side, vars, Q, linv), linv)

def while_wp(ast, vars, Q, linv):
    '''
    The weakest precondition for a while statement.
    '''
    cond = ast.subtrees[0]
    body = ast.subtrees[1]
    e = mk_env(vars)
    e_vals = list(e.values())
    return lambda env: And(linv(env),
                            ForAll(e_vals, And(
                                Implies(
                                    And(linv(e), get_expr_value(cond, e)), 
                                    globals()['get_weakest_precondition'](body, vars, linv, None)(e)),
                                Implies(
                                    And(linv(e), Not(get_expr_value(cond, e))),
                                    Q(e)))))

def if_wp(ast, vars, Q, linv):
    '''
    The weakest precondition for an if statement.
    '''
    cond = ast.subtrees[0]
    then = ast.subtrees[1]
    else_ = ast.subtrees[2]
    return lambda env: Or( And(get_expr_value(cond, env), globals()['get_weakest_precondition'](then, vars, Q, linv)(env)),
                            And(Not(get_expr_value(cond, env)), globals()['get_weakest_precondition'](else_, vars, Q, linv)(env)))

def assert_wp(ast, vars, Q, linv):
    '''
    The weakest precondition for an assert statement.
    '''
    cond = ast.subtrees[0]
    return lambda env: And(get_expr_value(cond, env), Q(env))

def get_weakest_precondition(ast, vars, Q, linv):
    '''
    Returns the weakest precondition for the given AST.
    '''
    match ast.root:
        case ':=':
            return assign_wp(ast, Q )
        case ';':
            return psicuda_wp(ast, vars, Q, linv)
        case 'while':
            return while_wp(ast, vars, Q, linv)
        case 'if':
            return if_wp(ast, vars, Q, linv)
        case 'assert':
            return assert_wp(ast, vars, Q, linv)
        case _:
            return Q
        
def solve(formulas):
    s = Solver()
    s.add(formulas)
    status = s.check()
    #if status == sat:
     #   print(s.model()) 
    return status == unsat

def verify(P, ast, Q, linv=None):
    """
    Verifies a Hoare triple {P} c {Q}
    Where P, Q are assertions (see below for examples)
    and ast is the AST of the command c.
    Returns `True` iff the triple is valid.
    Also prints the counterexample (model) returned from Z3 in case
    it is not.
    """
    vars = []
    [vars.append(x) for x in vars_from_ast(ast) if x not in vars]
    weakest_precondition = get_weakest_precondition(ast=ast, vars=vars, Q=Q, linv=linv)
    env = mk_env(vars)
    return solve(Not(Implies(P(env), weakest_precondition(env))))

if __name__ == '__main__':
    # example program
    #pvars = ['a', 'b', 'c']
    program = "a:= 0 ; b := 0 ; while b<10 do (a:= a + 2 ; b:= b + 1) ; assert a > 19"
    P = lambda d: True
    Q = lambda d: True
    linv = lambda d: d['a'] == 2 * d['b']

    #
    # Following are other programs that you might want to try
    #

    ## Program 1
    #pvars = ['x', 'i', 'y']
    #program = "y := 0 ; while y < i do ( x := x + y ; if (x * y) < 10 then y := y + 1 else skip )"
    #P = lambda d: d['x'] > 0
    #Q = lambda d: d['x'] > 0
    #linv = lambda d: **figure it out!**

    ## Program 2
    #pvars = ['a', 'b']
    #program = "while a != b do if a > b then a := a - b else b := b - a"
    #P = lambda d: And(d['a'] > 0, d['b'] > 0)
    #Q = lambda d: And(d['a'] > 0, d['a'] == d['b'])
    #linv = lambda d: a > 0  and b > 0

    ast = WhileParser()(program)

    if ast:
        print(">> Valid program.")
        # Your task is to implement "verify"
        print(verify(P, ast, Q, linv=linv))
    else:
        print(">> Invalid program.")