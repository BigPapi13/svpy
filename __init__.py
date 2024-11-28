import os
import importlib.util

## Global variables
writefile = None

def build(input_directory="src", output_directory="build", plugins: list = []):
    files = read_dir(input_directory)
    for f in files:
        f.process(output_directory, plugins)

# Reads through all the files in a subdirectory (defaults to current working directory)
#   - Returns a list of SVFile objects
def read_dir(directory="src"):
    file_list = []

    for filename in os.listdir(directory):
        f = SVFile(filename, directory)
        file_list.append(f)

    return file_list

def svwrite(line):
    global writefile
    writefile.write(str(line) + "\n")

# System verilog file class
class SVFile:
    def __init__(self, filename, directory=""):
        if directory != "":
            directory += "/"
        self.f = open(f"{directory}{filename}", 'r')
        self.name = filename
        self.directory = directory
        
    def process(self, output_directory="", plugins: list = []):
        if output_directory != "":
            output_directory += "/"

        if not os.path.exists(".svpy_temp"):
            os.makedirs(".svpy_temp")

        script_name = f".svpy_temp/{self.name}.py"
        tempfile = open(script_name, 'w')

        # Write headers
        tempfile.write("import svpy\n")
        tempfile.write("from svpy import svwrite\n")
        tempfile.write(f"svpy.writefile = open(\"{output_directory}{self.name}\", 'w')\n")

        # Import all plugins
        for plugin in plugins:
            tempfile.write("from " + plugin + " import *\n")

        # Paste contents into temp file
        in_block_macro = False
        for line in self.f:
            # Case 1: Currently in block macro
            if in_block_macro:
                if line.strip() == "$$$":  # Escape block macro
                    in_block_macro = False
                else:
                    tempfile.write(line)
            
            # Case 2: Single line macro signifier found
            elif line.strip()[:2] == "$ ":
                tempfile.write(line.replace("$ ", ""))  # Get rid of macro signifier and copy contents to output

            # Case 2: Block macro signifier found
            elif line.strip() == "$$$":
                in_block_macro = True
            else:
                # Look for inline macros
                line = process_inline_macros(line)

                # Just pass the line as an svwrite (basically passes directly to final file)
                tempfile.write(f"svwrite(\"{line[:-1]}\")\n")
                
        tempfile.write("svpy.writefile.close()")
        tempfile.close()

        # Run temp file
        if os.path.exists(script_name):
            spec = importlib.util.spec_from_file_location(script_name, script_name)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        # Cleanup
        os.remove(script_name)
            

# Helper function for replacing invalid characters
def process_line(line):
    line = line.replace('"', '\\"')
    return line

def process_inline_macros(line):
    ## Process:
    #   1. If a $$ is found, begin inline macro
    #       Replace first one with " +
    #       Replace second set with + "
    #   2. Contents of macro are passed directly

    open_flag = False
    while "$$" in line:
        open_flag = not open_flag
        if open_flag:
            line = line.replace("$$", '" + str(', 1)
        else:
            line = line.replace("$$", ') + "', 1)

    return line
