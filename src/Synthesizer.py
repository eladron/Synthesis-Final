import argparse
from wp import verify , vars_from_ast
from syntax import WhileParser
from adt.tree import Tree
import pandas as pd
from z3 import And
from linv_creator import LinvCreator
import os
from tqdm import tqdm

LOWER_BOUND = 0
UPPER_BOUND = 100
LOOPS_ITERATION = []
MAX_ITERAION = 10
ORIGINAL_PROGRAM = None
IS_INTERACTIVE = True
values_checked = []

def error(msg):
    print('Error:', msg)
    exit(1)

def count(ast: Tree, node: str):
    tmp = 1 if ast.root == node else 0
    for s in ast.subtrees:
        tmp += count(s, node)
    return tmp

def createAnd(d: dict, example: dict):
    if len(example) == 0:
        return True
    k, v = example.popitem()
    if pd.isna(v):
        return createAnd(d, example)
    if len(example) == 0:
        return d[k] == v
    return And(d[k] == v, createAnd(d, example))

def replace_hole(ast, value):
    if ast.root == 'hole':
        return Tree('num', [Tree(value)])
    else:
        new_ast = ast.clone()
        new_ast.subtrees = [replace_hole(s, value) for s in new_ast.subtrees]
        return new_ast
    
def loop_unroll(ast: Tree) -> Tree:
    global LOOPS_ITERATION
    if ast.root in ['while', 'while2']:
        if ast.root == 'while':
            LOOPS_ITERATION.append(0)
        else:
            LOOPS_ITERATION[-1] += 1
        if LOOPS_ITERATION[-1] > MAX_ITERAION:
            LOOPS_ITERATION.pop()
            return ast
        condition = ast.subtrees[0]
        body = ast.subtrees[1]
        if LOOPS_ITERATION[-1] == MAX_ITERAION:
            new_ast = Tree('if', [condition, body, Tree('skip', [])])
        else:
            tmp_ast = Tree('while2', [condition, body])
            body = Tree(';', [body, tmp_ast])
            new_ast = Tree('if', [condition, body, Tree('skip',[])])
        return loop_unroll(new_ast)
    else:
        return Tree(ast.root, [loop_unroll(s) for s in ast.subtrees])

def try_again():
    global LOWER_BOUND, UPPER_BOUND
    if not IS_INTERACTIVE:
        return False
    flag = input('Do you want to try again with different bounds? (y/n): ')
    while flag not in ['y', 'n']:
        print('Invalid input')
        flag = input('Do you want to try again with different bounds? (y/n): ')
    if flag == 'y':
        while True:
            LOWER_BOUND = int(input('Enter lower bound: '))
            UPPER_BOUND = int(input('Enter upper bound: '))
            if LOWER_BOUND < UPPER_BOUND:
                break
            print('Invalid bounds, lower bound must be less than upper bound')
        return True
    return False
    
'''
PBE
''' 
def verify_example(program, input_example, output_example, linv):
    vars = vars_from_ast(program)
    P = lambda d: createAnd(d, {v:k for (v,k) in input_example.to_dict().items() if v in vars})
    Q = lambda d: createAnd(d, {v:k for (v,k) in output_example.to_dict().items() if v in vars})
    
    return verify(P, program, Q, linv)

def pbe(ast, input_examples_file, output_examples_file, linv):
    global LOWER_BOUND, UPPER_BOUND
    input_examples = pd.read_excel(input_examples_file)
    output_examples = pd.read_excel(output_examples_file)
    if (input_examples.shape[0] != output_examples.shape[0]):
        error('number of input examples must be equal to number of output examples')
    num_examples = len(input_examples)
    print(f'Number of examples: {num_examples}')
    while True:
        to_check = [*range(LOWER_BOUND, UPPER_BOUND + 1)]
        to_check = filter(lambda x: x not in values_checked, to_check)
        for i in to_check:
            values_checked.append(i)
            new_ast = replace_hole(ast, i)
            counter = 0
            for j in range(num_examples):
                if verify_example(new_ast, input_examples.iloc[j], output_examples.iloc[j], linv):
                    counter += 1
                    continue
                break
            # number satisfied all examples
            if counter == num_examples:
                print('Found a solution!')
                print(f"?? = {i}")
                print('New Program:')
                print(ORIGINAL_PROGRAM.replace('??', str(i)))
                return
        print(f'No solution found in the range [{LOWER_BOUND}, {UPPER_BOUND}] ')
        if not try_again():
            return
'''
Asserts
'''     
def verify_asserts(ast, linv=None):
    P = lambda d: True
    Q = lambda d: True
    
    return verify(P, ast, Q, linv)

def assert_synthesis(ast, linv):
    global LOWER_BOUND, UPPER_BOUND
    while True:
        to_check = [*range(LOWER_BOUND, UPPER_BOUND + 1)]
        to_check = filter(lambda x: x not in values_checked, to_check)
        for i in to_check:
            values_checked.append(i)
            new_ast = replace_hole(ast, i)
            if verify_asserts(new_ast, linv):
                print('Found a solution!')
                print(f"?? = {i}")
                print('New Program:')
                print(ORIGINAL_PROGRAM.replace('??', str(i)))
                return
        print(f'No solution found in the range [{LOWER_BOUND}, {UPPER_BOUND}]')
        if not try_again():
            return
    
def main():
    global LOWER_BOUND, UPPER_BOUND, MAX_ITERAION, ORIGINAL_PROGRAM, IS_INTERACTIVE
    parser = argparse.ArgumentParser(description='Synthesizer for programs in WHILE-LANG. The synthesizer can use PBE and Asserts to fill the holes in the program.')
    parser.add_argument('-p', '--program', default='program.txt', help='Path to file containing the program (path from main folder), default is program.txt')
    parser.add_argument('-ub', '--upper_bound', type=int, default=100 ,help='upper bound for the numbers checking, default is 100')
    parser.add_argument('-lb', '--lower_bound', type=int, default=0 ,help='lower bound for the numbers checking, default is 0')
    parser.add_argument('-pbe', '--programing_by_example', action='store_true', help='Indicates the use of programming by examples to synthesize the program')
    parser.add_argument('-ife','--input_file_examples', default='input_file_examples.txt' ,help='Path to file containing the input examples (path from main folder), default is input_file_examples.txt')
    parser.add_argument('-ofe','--output_file_examples', default='output_file_examples.txt' ,help='Path to file containing the output examples (path from main folder), default is output_file_examples.txt')
    parser.add_argument('-lu', '--loop_unrolling', type=int, default=0 ,help='number of iterations for loop unrolling - Suppose to be the number of iterations in the program')
    parser.add_argument('-lf', '--linv_file', default='', help='file containing the linv, Should be located in linv folder')
    parser.add_argument('-ni', '--no_interactive', action='store_true', help='Indicates that the synthesizer should not ask for input')

    args = parser.parse_args()
    program = open(args.program, 'r').read()
    ORIGINAL_PROGRAM = program
    print('Program to fill: \n' + program)
    ast = WhileParser()(program)
    linv = None
    IS_INTERACTIVE = not args.no_interactive
    
    if not ast:
        error('Invalid program')

    if count(ast, 'hole') == 0:
        error('Program does not have any holes, Nothing to synthesize')
    
    if count(ast, 'while') > 1:
        error('Program can not have more than one while loop')
    
    if args.upper_bound < args.lower_bound:
        error('upper bound must be greater than lower bound')

    if count(ast, "while") == 1:
        if args.loop_unrolling > 0 and args.linv_file != '':
            error("loop unrolling and loop invariant can not be used at the same time")
        if args.loop_unrolling == 0:
            file_path = 'linv/'
            name = args.linv_file
            lc = LinvCreator()
            if args.no_interactive:
                if name == '':
                    error('You did not enter linv file name')
                file_path += name
                if not os.path.exists(file_path):
                    error('linv file does not exist')
            else: 
                if args.linv_file == '':
                    name = input('You did not enter linv file name, enter name or press enter to use default name(linv.json): ')
                    if name == '':
                        name = 'linv.json'
                file_path += name
                if not os.path.exists(file_path):
                    print('linv file does not exist, creating new one')
                    lc.createLinv(name)
                else:
                    flag = input('linv file already exists, do you want to override it? (y/n): ')
                    while flag not in ['y', 'n']:
                        print('Invalid input')
                        flag = input('linv file already exists, do you want to override it? (y/n): ')
                    if flag == 'y':
                        lc.createLinv(name)
            linv = lc.getLinv(name)
        else:
            MAX_ITERAION = args.loop_unrolling
            ast = loop_unroll(ast)

    LOWER_BOUND = args.lower_bound
    UPPER_BOUND = args.upper_bound
    if args.programing_by_example:
        if not args.input_file_examples or not args.output_file_examples:
            error('examples files are required for PBE')
        if not os.path.exists(args.input_file_examples):
            error('input examples file does not exist')
        if not os.path.exists(args.output_file_examples):
            error('output examples file does not exist')
        pbe(ast, args.input_file_examples, args.output_file_examples, linv)
    else:
        assert_synthesis(ast, linv)

if __name__ == '__main__':
    main()
    