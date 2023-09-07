# Synthesis - Final Project

## Description
Our synthesizer, written in Python, can fill holes (which represent unknown integers) in the WHILE-LANG program.
The synthesizer fills holes according to examples (Programming by Example), assertions inside the program, and loop unrolling.


## Usage

command line:
```bash
python3 ./src/Synthesizer.py
```

### Options

* -h, --help: Shows help message and exit.
* -p, --program: The path to the file containing the program with the holes.
* -lb, --lower_bound: The lower bound for the number checking. The default is 0.
* -ub, --uower_bound: The upper bound for the number checking. The default is 100.
* -pbe, --programin_by_example: Indicates using PBE to synthesize the holes.
* -ife, --input_file_examples: The path to an Excel file containing the input examples.
* -ofe, --onput_file_examples: The path to an Excel file containing the input examples.
* -lf, --linv_file: The path to the file containing a JSON file containing the loop invariant. The path is calculated from the linv folder. 
* -lu, --loop_unrolling:  If the value isn't 0, then loop unrolling will be used and will unroll the loop *value* number of times.

### Input/Output examples files format

The input/output examples files should be in Excel format and structured as follows:
![image](https://github.com/eladron/Synthesis-Final/assets/63602693/4171039d-8b66-47a8-a1c7-2732b1c9c44c)

Each line in both files should represent an input/output example, and there should be the same number of examples (lines) in both files.
If a cell is empty, it will not affect this specific example.

### Linv file format


The linv files that should be located under the linv folder are in JSON format.
An example of a linv file:

![image](https://github.com/eladron/Synthesis-Final/assets/63602693/83463c5d-3f7c-49c7-a0b1-c97b08256dc3)

The tag field has 3 available values: 'And', 'Or', and 'expr'.
If a tag is equal to 'expr' then it will have a brother named 'expr' that will contain a list with 3 places: [EXPR, RELOP, EXPR] where RELOP is one of ['==', '!=', '>', '>=', '<', '<='] and expr is an expression written in python syntax.

### Linv file creation

Because the linv files can be complicated, we added a file creator script that enables you to create a linv file interactively.

#### Usage:

```python
from linv_creator import LinvCreator
lc = LinvCreator()
lc.createLinv('linv.json') # Interactivly create a linv file and put it in the linv folder.
linv = lc.getlinv('linv.json') # Returns a lambda function that represents the loop invariant written in the file
```

You can also use the command line:
```bash
python3 ./src/linv_creator.py -f=<File Name>
```

## Benchmarks
The supplied benchmarks are in the [Benchmarks folder](Benchmarks/).
Adding more benchmarks can be done by creating a new folder under the [Benchmarks folder](Benchmarks/), and adding a program with holes in 'program.txt'. Adding 'input.xlsx' and 'output.xlsx if the benchmarks are about pbe, add a linv folder containing a JSON file containing the linv file in the correct format and a command.txt having the full command to run.

### Running Benchmarks
To run all of the benchmarks, use the supplied script: run.py.
```bash
python3 run.py 
```
The script will output to the screen the results for the benchmarks including the synthesized programs and how long it took to synthesize them.
In order to redirect the output, use the flag -o with the name of the output file. For example:
```bash
python3 run.py -o='output.txt'
```
You can also run specific benchmarks by adding their names to the command line.
```bash
python3 run.py 'Assert in while' 'If else'
```
**Note that running all of the benchmarks might take a few minutes.**

## Cool Implementation Details
* The first thing we would like to highlight is the support of both assert and pbe combine, which means a user can give examples and put asserts in the program to synthesize the holes.
* The second thing is the Synthesizer is very interactive, The user can help the synthesizer with which numbers to fill the holes (If the synthesizer doesn't find a suitable number, the user can ask for a different range of numbers).
* The synthesizer can handle loops in two different ways:
  * An average user can give the number of iterations the loops should happen and give that number in the lf argument which will cause the loop to unroll and will replace it with a series of ifs.
  * An advanced user can create a loop invariant using the linv_creator. This will help the Synthesizer to produce better results.


## Contributors

* Elad Ron
* Eilon Tal
