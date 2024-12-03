import os
import importlib.util

## Global variables
writefile = None

def build(input_directory="src", output_directory="build", plugins: list = []):
    files = read_dir(input_directory)

    if not os.path.exists(output_directory) and output_directory != "":
        os.makedirs(output_directory)

    for f in files:
        f.process(output_directory, plugins)

# Reads through all the files in a subdirectory (defaults to current working directory)
#   - Returns a list of SVFile objects
def read_dir(directory="src"):
    file_list = []

    for filename in os.listdir(directory):
        if filename[-3:] == ".sv" or filename[-2:] == ".v":
            f = SVFile(filename, directory)
            file_list.append(f)

    return file_list

def svwrite(*args):
    global writefile
    for line in args:
        if line != None:
            writefile.write(str(line))

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
            tempfile.write("import " + plugin + "\n")

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

            # Case 3: Block macro signifier found
            elif line.strip() == "$$$":
                in_block_macro = True

            # Case 4: Normal line (still need to check for inline macros)
            else:
                if iscomment(line):
                    line = process_line(line)

                substrings = line.split("$$")
                
                open_flag = False
                for string in substrings:
                    if not open_flag:  # Normal text
                        tempfile.write(f"svwrite(\"{string}\")".replace("\n", "\\n") + "\n")
                    else: # Inline macro
                        tempfile.write(f"svwrite({string})" + "\n")
                        

                    open_flag = not open_flag
                
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


def iscomment(line):
    if line.strip()[:2] == "//":
        return True
    return False