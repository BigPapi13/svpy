# SVPY
**What is SVPY?**

SVPY is a simple python-based precompiler used to accelerate the process of coding in Verilog/System Verilog. It allows for easy insertion of python code into SV files, and can be highly customized with plugins.

## Basic Usage
When a file is processed by SVPY, each line in the SV file is simply passed along to the output file unless a **macro** is specified. If a macro is found, that line is instead interpreted as python code.

To write something to the output file with python, you can use `svwrite(line)` to dynamically write a line to the output. Some examples of macro usage are as follows:

```sv
// Any line starting with "$ " is a macro
$ x = 1
$ y = 2
$ svwrite("logic foo = " + str(x + y))

// Triple dollar signs indicate block macro
$$$
from math import cos
svwrite(f"real theta = {cos(1)}")

def scaled_add(a, b):
  return f"{a} << 4 + {b} << 4"
$$$

// $$<code>$$ Can be for inline macros, where <code> is automatically evaluated and inserted into the line
logic a = $$3 + 4$$
logic b = $$12 / 3$$
logic test = $$scaled_add("a", "b")$$
```

Running the above code blocks through SVPY produces the following output:
```sv
// Any line starting with "$ " is a macro
logic foo = 3

// Triple dollar signs indicate block macro
real theta = 0.5403023058681398

// $$<code>$$ Can be for inline macros, where <code> is automatically evaluated and inserted into the line
logic a = 7
logic b = 4.0
logic test = a << 4 + b << 4
```

## Environment Setup
Running SVPY simply requires running a Python file that calls the `build()` command. An example file can be seen below:

```py
from svpy import build

build(input_directory="src", output_directory="build", plugins=["my_plugin1", "my_plugin2"])
```
**Result:**
- All files in the filepath `input_directory` are processed
- The processed files are placed in `output_directory` (file names are echoed from input)
- The plugins listed in `plugins` are automatically imported for every file processed

## Plugins

Plugins are simply python modules that can be imported into an svpy project and are accessible from the processed SV files. An example plugin can be seen below:

`to_bits.py`
```py
__all__ = [
    "to_bits"
]

from math import floor

# Converts a decimal value into binary
def to_bits(value, bits=16, precision=0):
    value = value * (2**precision)

    output = ""

    value = floor(value)
    for i in range(bits):
        output = (str(value % 2)) + output
        value = floor(value / 2)

    return f"{bits}'b" + output
```

If `to_bits.py` were included in the plugins list, then the `to_bits` function would be made available to all SV files. Plugins can be imported from any paths accessible by the current python context.

_Note: This isn't much different than simply importing python modules normally, which is also possible. I just thought plugins made it sound cooler and more extensible._
