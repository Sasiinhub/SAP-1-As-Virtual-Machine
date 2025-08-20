"""
SAP-1 Virtual Machine (Python) – v2 (with STA)
---------------------------------------------
Now includes STA (store accumulator into memory) instruction, needed for
assignments in toy compiler.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

# --- Utility helpers ---------------------------------------------------------

def u8(x: int) -> int:
    return x & 0xFF

def u4(x: int) -> int:
    return x & 0xF

# --- CPU definition ----------------------------------------------------------

@dataclass
class SAP1:
    memory: List[int] = field(default_factory=lambda: [0]*16)

    A: int = 0
    B: int = 0
    OUT: int = 0
    IR: int = 0
    PC: int = 0
    MAR: int = 0

    halted: bool = False
    t_state: int = 0

    trace_instructions: bool = True
    trace_microsteps: bool = False

    def reset(self):
        self.A = self.B = self.OUT = self.IR = 0
        self.PC = self.MAR = 0
        self.halted = False
        self.t_state = 0

    def _fetch_cycle(self) -> None:
        self.MAR = u4(self.PC)
        if self.trace_microsteps:
            print(f"T0: MAR <- PC = {self.PC:01X}")
        self.t_state = 1
        self.IR = u8(self.memory[self.MAR])
        if self.trace_microsteps:
            print(f"T1: IR <- M[MAR] = {self.IR:02X}; PC <- PC+1")
        self.PC = u4(self.PC + 1)
        self.t_state = 2

    def _decode(self) -> Tuple[int, int]:
        opcode = (self.IR >> 4) & 0xF
        addr = self.IR & 0xF
        if self.trace_microsteps:
            print(f"T2: Decode -> opcode={opcode:X}, addr={addr:X}")
        self.t_state = 3
        return opcode, addr

    # --- Instruction implementations ---------------------------------------
    def _exec_LDA(self, addr: int):
        self.MAR = u4(addr)
        self.A = u8(self.memory[self.MAR])
        self.t_state = 0

    def _exec_ADD(self, addr: int):
        self.MAR = u4(addr)
        self.B = u8(self.memory[self.MAR])
        self.A = u8(self.A + self.B)
        self.t_state = 0

    def _exec_SUB(self, addr: int):
        self.MAR = u4(addr)
        self.B = u8(self.memory[self.MAR])
        self.A = u8(self.A - self.B)
        self.t_state = 0

    def _exec_STA(self, addr: int):
        self.MAR = u4(addr)
        self.memory[self.MAR] = u8(self.A)
        self.t_state = 0

    def _exec_OUT(self):
        self.OUT = u8(self.A)
        self.t_state = 0

    def _exec_HLT(self):
        self.halted = True
        self.t_state = 0

    def step(self) -> Optional[str]:
        if self.halted:
            return None

        self._fetch_cycle()
        opcode, addr = self._decode()

        trace_msg = None
        if opcode == 0x1:
            trace_msg = f"LDA {addr:X}"
            self._exec_LDA(addr)
        elif opcode == 0x2:
            trace_msg = f"ADD {addr:X}"
            self._exec_ADD(addr)
        elif opcode == 0x3:
            trace_msg = f"SUB {addr:X}"
            self._exec_SUB(addr)
        elif opcode == 0x4:
            trace_msg = f"STA {addr:X}"
            self._exec_STA(addr)
        elif opcode == 0xE:
            trace_msg = f"OUT (A={self.A:02X})"
            self._exec_OUT()
        elif opcode == 0xF:
            trace_msg = "HLT"
            self._exec_HLT()
        else:
            raise ValueError(f"Unknown opcode {opcode:X} in IR={self.IR:02X}")

        if self.trace_instructions:
            return f"PC={self.PC:01X} IR={self.IR:02X} A={self.A:02X} B={self.B:02X} OUT={self.OUT:02X} :: {trace_msg}"
        return None

    def run(self, max_steps: int = 1000) -> List[str]:
        trace: List[str] = []
        steps = 0
        while not self.halted and steps < max_steps:
            msg = self.step()
            if msg:
                trace.append(msg)
            steps += 1
        return trace

    def load_program(self, bytes_at_addresses: List[Tuple[int, int]]):
        for addr, byte in bytes_at_addresses:
            self.memory[u4(addr)] = u8(byte)

# --- Tiny Assembler ----------------------------------------------------------

class AsmError(Exception):
    pass

OPCODES: Dict[str, int] = {
    'LDA': 0x1,
    'ADD': 0x2,
    'SUB': 0x3,
    'STA': 0x4,
    'OUT': 0xE,
    'HLT': 0xF,
}

def assemble(lines: List[str]) -> List[int]:
    cleaned = []
    for raw in lines:
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        cleaned.append(line)

    labels: Dict[str, int] = {}
    pc = 0
    items: List[Tuple[str, Optional[str]]] = []

    for line in cleaned:
        if line.endswith(':'):
            labels[line[:-1].strip()] = pc
            continue
        parts = line.replace(',', ' ').split()
        head = parts[0].upper()
        if head == '.BYTE':
            items.append(('.BYTE', parts[1]))
            pc += 1
        elif head in OPCODES:
            opnd = parts[1] if len(parts) > 1 else None
            items.append((head, opnd))
            pc += 1
        else:
            raise AsmError(f"Unknown directive or mnemonic: {head}")

    def parse_addr(tok: str) -> int:
        if tok is None:
            return 0
        if tok in labels:
            return labels[tok]
        return int(tok, 0)

    out: List[int] = []
    for mnemonic, opnd in items:
        if mnemonic == '.BYTE':
            val = int(opnd, 0) & 0xFF
            out.append(val)
            continue
        opcode = OPCODES[mnemonic]
        if mnemonic in ('OUT', 'HLT'):
            byte = (opcode << 4)
        else:
            addr = parse_addr(opnd)
            byte = ((opcode & 0xF) << 4) | (addr & 0xF)
        out.append(byte)

    return out

# --- Demo -------------------------------------------------------------------

def demo_program_sta() -> List[str]:
    asm = [
        '        LDA a',
        '        ADD b',
        '        STA c',
        '        LDA c',
        '        OUT',
        '        HLT',
        'a:      .byte 5',
        'b:      .byte 7',
        'c:      .byte 0',
    ]
    code = assemble(asm)
    cpu = SAP1()
    for i, byte in enumerate(code):
        cpu.memory[i] = byte & 0xFF
    trace = cpu.run()
    trace.append(f"FINAL: A={cpu.A:02X} OUT={cpu.OUT:02X} halted={cpu.halted}")
    return trace

if __name__ == '__main__':
    print("SAP-1 VM demo with STA: a=5, b=7 -> c=12 -> OUT=12")
    logs = demo_program_sta()
    for line in logs:
        print(line)
