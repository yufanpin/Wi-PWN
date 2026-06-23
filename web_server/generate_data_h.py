#!/usr/bin/env python3
"""
Replacement for auto_generate.exe (cross-platform).
Usage:
  python web_server/generate_data_h.py <input_dir> <output_file>

Where <input_dir> is the Jekyll output directory (e.g., web_server/output/html/).
Generates a C header file with gzip-compressed PROGMEM byte arrays suitable for ESP8266 firmware.
"""

import os
import sys
import gzip

def generate_data_h(input_dir, output_path):
    files = []
    for root, dirs, filenames in os.walk(input_dir):
        for f in sorted(filenames):
            full = os.path.join(root, f)
            # Skip hidden files and non-web files
            if f.startswith('.') or f.endswith('.map') or f.endswith('.json'):
                continue
            files.append(full)

    with open(output_path, 'w', encoding='utf-8') as out:
        out.write('// Auto-generated from web assets - DO NOT EDIT BY HAND\n')
        out.write(f'// Source: {input_dir}\n\n')
        out.write('#include <avr/pgmspace.h>\n\n')

        for fpath in files:
            rel = os.path.relpath(fpath, input_dir)
            # Convert path to C identifier
            name = rel.replace('\\', '/').replace('/', '_').replace('.', '_').upper()
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

    print(f'Generated {output_path} with {len(files)} files from {input_dir}')
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
