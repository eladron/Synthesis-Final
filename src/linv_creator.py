from z3 import And, Or
import json
import os
import argparse

class LinvCreator:

    def __init__(self):
        self.current_linv = ''
        self.stack_condition = []
    
    def _print_current_linv(self):
        print('Current Linv:', self.current_linv)

    def _check_simple_cond(self, cond_split):
        if len(cond_split) != 3:
            print('Invalid condition, simple condition must have 2 expressions and 1 operator with a space between them')
            return True
        if cond_split[1] not in ['==', '!=', '>', '<', '>=', '<=']:
            print('Invalid operator in the condition')
            return True
        return False
    
    def _create_linv_aux(self, data: dict):
        flag = input("Is it And or Or condition? (y/n): ")
        while flag not in ['y', 'n']:
            print('Invalid input')
            flag = input("Is it And or Or condition? (y/n): ")
        if flag == 'y':
            self.stack_condition.append(2)
            is_and = input("Is it And condition? (y/n): ")
            while is_and not in ['y', 'n']:
                print('Invalid input')
                is_and = input("Is it And condition? (y/n): ")
            tag = 'And' if is_and == 'y' else 'Or'
            self.current_linv = self.current_linv + f'{tag}('
            self._print_current_linv()
            data['tag'] = tag
            data['children'] = [self._create_linv_aux({})]
            data['children'].append(self._create_linv_aux({}))
        else:
            cond = input('Enter simple condition: (Have spaces between expressions and boolean operators): ')
            cond_split = cond.split(' ')
            while self._check_simple_cond(cond_split):
                cond = input('Enter simple condition: (Have spaces between expressions and operators): ')
                cond_split = cond.split(' ')
            while cond_split[1] not in ['==', '!=', '>', '<', '>=', '<=']:
                print('Invalid operator in the condition')
            self.current_linv = self.current_linv + f'{cond_split[0]} {cond_split[1]} {cond_split[2]}'
            if len(self.stack_condition) != 0:
                if self.stack_condition[-1] == 2:
                    self.current_linv = self.current_linv + ', '
                    self.stack_condition[-1] = 1
                else:
                    while len(self.stack_condition) != 0 and self.stack_condition[-1] == 1:
                        self.current_linv = self.current_linv + ')'
                        self.stack_condition.pop()
            self._print_current_linv()
            data['tag'] = 'expr'
            data['expr'] = cond_split
        return data
    
    def createLinv(self, file = 'linv.json'):
        self.current_linv = ''
        self.stack_condition = []
        data = {"linv" : self._create_linv_aux({})}
        file_path = 'linv/' + file   
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def _createCondition(self, d: dict, data: dict):
        if data['tag'] not in ['expr', 'And', 'Or']:
            print('Error: Invalid condition, tag must be expr, And or Or')
            exit(1)
        if data['tag'] == 'expr':
            cond = data['expr']
            if len(cond) != 3:
                print('Error: Invalid condition, simple condition must have a list of 3 elements')
                exit(1)
            if cond[1] not in ['==', '!=', '>', '<', '>=', '<=']:
                print('Error: Invalid operator in the condition')
                exit(1)
            operators = {
                '==': eval(cond[0],d) == eval(cond[2],d),
                '!=': eval(cond[0],d) != eval(cond[2],d),
                '>': eval(cond[0],d) > eval(cond[2],d),
                '<': eval(cond[0],d) < eval(cond[2],d),
                '>=': eval(cond[0],d) >= eval(cond[2],d),
                '<=': eval(cond[0],d) <= eval(cond[2],d)
            }
            return operators[cond[1]]
        else:
            if len(data['children']) != 2:
                print('Error: Invalid condition, Complex condition must have 2 children')
                exit(1)
            if data['tag'] == 'And':
                return And(self._createCondition(d, data['children'][0]), self._createCondition(d, data['children'][1]))
            else:
                return Or(self._createCondition(d, data['children'][0]), self._createCondition(d, data['children'][1]))

    def getLinv(self, file='linv.json'):
        file_path = 'linv/' + file
        if not os.path.exists(file_path):
            print('Error: linv file not found')
            exit(1)
        with open(file_path, 'r') as f:
            data = json.load(f)
        return lambda d: self._createCondition(d, data['linv'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create Loop Invariant File')
    parser.add_argument('-f', '--file', type=str, default='linv.json', help='linv file name')
    args = parser.parse_args()
    linv_creator = LinvCreator()
    linv_creator.createLinv(args.file)