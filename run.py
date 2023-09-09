import os
import shutil
import time
import sys

BENCHMARKS_PATH = 'Benchmarks/'

def clear_commands(path):
    if os.path.exists(path + 'command.txt'):
        os.remove(path + 'command.txt')

def print_to_output_file(output_file, content):
    if output_file:
        with open(output_file, 'a') as f:
            f.write(content + '\n')
    else:
        print(content)

def clean_benchmark(path, linv_file, examples):
    os.remove('program.txt')
    if linv_file != '':
        os.remove('linv/' + linv_file)
    if examples:
        os.remove('input.xlsx')
        os.remove('output.xlsx')

def add_flags(command, path):
    ex_file = open(path + 'Explanation.txt', 'r')
    content = ex_file.read()
    splited = content.split(' ')
    for s in splited:
        if '-lu' in s:
            command += ' -lu=' + s.split('=')[1]
        if '-lb' in s:
            command += ' -lb=' + s.split('=')[1]
        if '-ub' in s:
            command += ' -ub=' + s.split('=')[1]
    ex_file.close()
    return command.replace('\n', '')

def run_benchmark(benchmark_folder, output_file):
    path = BENCHMARKS_PATH + benchmark_folder + '/'
    shutil.copy(path + 'program.txt','program.txt')
    files = os.listdir(path)
    linv_file = os.listdir(path + 'linv')[0] if 'linv' in files else ''
    examples = 'input.xlsx' in files and 'output.xlsx' in files
    if linv_file != '':
        shutil.copy(path + 'linv/' + linv_file, 'linv/' + linv_file)
    if examples:
        shutil.copy(path + 'input.xlsx', 'input.xlsx')
        shutil.copy(path + 'output.xlsx', 'output.xlsx')
    if 'command.txt' in files:
        with open(path + 'command.txt', 'r') as f:
            command = f.read()
    else:
        command = "python3 ./src/Synthesizer.py -ni -p=program.txt " + (linv_file != '') * ("-lf=" + linv_file)
        command = command if not examples else command + " -pbe -ife=input.xlsx -ofe=output.xlsx"
        command = add_flags(command, path)
        with open(path + 'command.txt', 'w') as f:
            f.write(command)
    if output_file:
        command += ' >> ' + output_file
    st = time.time()
    os.system(command)
    print_to_output_file(output_file, f"Time: {time.time() - st} seconds")
    clean_benchmark(path, linv_file, examples)


if __name__ == '__main__':
    argv = sys.argv
    output_file = None
    benchmarks = []
    for arg in argv[1:]:
        if '-o='==arg[:3]:
            output_file = arg[3:]
            if os.path.exists(output_file):
                os.remove(output_file)
        else:
            benchmarks.append(arg)
    if len(benchmarks) == 0:
        benchmarks = os.listdir(BENCHMARKS_PATH)
    for benchmark_folder in benchmarks:
        if os.path.isdir(BENCHMARKS_PATH + benchmark_folder):
            # clear_commands(BENCHMARKS_PATH + benchmark_folder + '/') # Only needed if you want to clear the command.txt
            print_to_output_file(output_file, f"Benchmark {benchmark_folder}")
            run_benchmark(benchmark_folder, output_file)
            print_to_output_file(output_file, '----------------------------------------')

