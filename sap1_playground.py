# sap1_playground.py
# Combine Compiler + SAP-1 VM + Interactive Runner

# ---------------- COMPILER ----------------
def compile_toy(source):
    lines = [line.strip() for line in source.split(";") if line.strip()]
    assembly = []
    variables = {}
    mem_ptr = 0x0E  # start storing variables near top of memory (14, 15, etc.)
    
    for line in lines:
        if line.startswith("print"):
            var = line.split()[1]
            addr = variables[var]
            assembly.append(f"    LDA {addr}")
            assembly.append(f"    OUT")
        elif "=" in line:
            left, right = [p.strip() for p in line.split("=")]
            if "+" in right:
                a, b = [p.strip() for p in right.split("+")]
                addr_a, addr_b = variables[a], variables[b]
                assembly.append(f"    LDA {addr_a}")
                assembly.append(f"    ADD {addr_b}")
                variables[left] = mem_ptr
                assembly.append(f"    STA {mem_ptr}")
                mem_ptr -= 1
            else:  # assignment of constant
                if right.isdigit():
                    variables[left] = mem_ptr
                    assembly.append(f"    LDA #{right}")
                    assembly.append(f"    STA {mem_ptr}")
                    mem_ptr -= 1
                else:
                    variables[left] = variables[right]

    assembly.append("    HLT")
    return "\n".join(assembly)


# ---------------- VM ----------------
def run(assembly):
    memory = [0] * 16
    acc = 0
    pc = 0
    output = []

    # tiny assembler: parse our fake assembly
    code = []
    for line in assembly.splitlines():
        line = line.strip()
        if not line or line.startswith("."): 
            continue
        parts = line.split()
        if parts[0] == "LDA":
            if parts[1].startswith("#"):
                code.append(("LDA_IMM", int(parts[1][1:])))
            else:
                code.append(("LDA", int(parts[1])))
        elif parts[0] == "STA":
            code.append(("STA", int(parts[1])))
        elif parts[0] == "ADD":
            code.append(("ADD", int(parts[1])))
        elif parts[0] == "OUT":
            code.append(("OUT", None))
        elif parts[0] == "HLT":
            code.append(("HLT", None))

    # execute
    while pc < len(code):
        instr, arg = code[pc]
        if instr == "LDA":
            acc = memory[arg]
        elif instr == "LDA_IMM":
            acc = arg
        elif instr == "STA":
            memory[arg] = acc
        elif instr == "ADD":
            acc = (acc + memory[arg]) & 0xFF
        elif instr == "OUT":
            print(f"OUT = {acc}")
            output.append(acc)
        elif instr == "HLT":
            break
        pc += 1

    return output


# ---------------- INTERACTIVE ----------------
if __name__ == "__main__":
    print("Welcome to SAP-1 Playground 🚀")
    print("Write your program in the toy language. End input with an empty line.\n")
    user_code = []
    while True:
        line = input(">>> ")
        if not line.strip():
            break
        user_code.append(line)

    source = "\n".join(user_code)
    assembly = compile_toy(source)

    print("\n--- Generated Assembly ---")
    print(assembly)
    print("\n--- Running on SAP-1 VM ---")
    run(assembly)
