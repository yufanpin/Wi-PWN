#!/usr/bin/env python3
"""
Replacement for auto_generate.exe (cross-platform).
Usage:
  python web_server/generate_data_h.py <input_dir> <output_file>

Where <input_dir> is the Jekyll output directory (e.g., web_server/output/html/).
Processes ONLY root-level files (not language subdirectories) and preserves the
existing data.h preamble (header guard, includes, variable declarations).
"""

import os
import sys
import gzip

def generate_data_h(input_dir, output_path):
    # Collect root-level files only (skip subdirectories = other languages)
    files = []
    for f in sorted(os.listdir(input_dir)):
        full = os.path.join(input_dir, f)
        if not os.path.isfile(full):
            continue
        if f.startswith('.') or f.endswith('.map') or f.endswith('.json'):
            continue
        files.append(full)

    # Read existing data.h preamble (everything up to and including /*auto_generator*/)
    # If file doesn't exist yet, generate minimal preamble
    preamble = ''
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        idx = content.find('/*auto_generator*/')
        if idx != -1:
            preamble = content[:idx] + '/*auto_generator*/\n'
        else:
            # Include up to the first const declaration
            idx = content.find('const char ')
            if idx != -1:
                preamble = content[:idx]
            else:
                preamble = content
    else:
        preamble = (
            '#ifndef data_h\n'
            '#define data_h\n'
            '#include "Settings.h"\n'
            '\n'
            'extern Settings settings;\n'
            '\n'
            'static uint8_t data_macBuffer;\n'
            'static char data_vendorBuffer;\n'
            'static String data_vendorStrBuffer = "";\n'
            '\n'
            '#define bufSize 2000\n'
            'int bufc = 0;\n'
            '\n'
            'char data_websiteBuffer[bufSize];\n'
            '\n'
            '/*\n'
            '  PROGMEM storage for web assets.\n'
            '  Auto-generated - do not edit by hand.\n'
            '*/\n'
            '\n'
            '/*auto_generator*/\n'
        )

    # Write output
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(preamble)

        for fpath in files:
            fname = os.path.basename(fpath)
            # Convert filename to C identifier
            name = fname.replace('.', '_').upper()
            c_name = f'data_{name}'

            # Read and gzip compress
            with open(fpath, 'rb') as f:
                raw = f.read()
            compressed = gzip.compress(raw)

            # Write PROGMEM array
            out.write(f'const char {c_name}[] PROGMEM = {{')
            for i, b in enumerate(compressed):
                if i % 16 == 0:
                    out.write('\n')
                out.write(f'0x{b:02X},')
            out.write('\n};\n\n')

        out.write('/*end_auto_generator*/\n')

    print(f'Generated {output_path} with {len(files)} root-level files from {input_dir}')
    return len(files)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: generate_data_h.py <input_dir> <output_file>')
        sys.exit(1)

    input_dir = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f'Error: input directory not found: {input_dir}')
        sys.exit(1)

    generate_data_h(input_dir, output_file)
