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

# Language subdirectory names to skip (these are translations, not root assets)
LANGUAGE_DIRS = {
    'english', 'german', 'russian', 'italian', 'dutch', 'portuguese',
    'slovak', 'polish', 'estonian', 'hebrew', 'czech', 'turkish', 'indonesia',
}

def generate_data_h(input_dir, output_path):
    # Collect all files recursively, skipping language subdirectories.
    # Use basename only for C variable names (so js/attack.js -> data_attack_JS).
    files = []  # list of (basename, full_path)
    seen_names = set()
    for root, dirs, filenames in os.walk(input_dir):
        # Skip language subdirectories in-place
        dirs[:] = [d for d in dirs if d not in LANGUAGE_DIRS]
        for f in sorted(filenames):
            if f.startswith('.') or f.endswith('.map') or f.endswith('.json'):
                continue
            full = os.path.join(root, f)
            # Use basename (not relative path) so js/attack.js -> attack.js
            if f not in seen_names:
                seen_names.add(f)
                files.append(full)

    # Read existing data.h to extract:
    # 1. preamble - everything up to and including /*auto_generator*/
    # 2. postamble - everything from /*end_auto_generator*/ onward (vendor list, #endif)
    preamble = ''
    postamble = '\n/*end_auto_generator*/\n\n#endif\n'
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Preamble: everything up to /*auto_generator*/
        idx = content.find('/*auto_generator*/')
        if idx != -1:
            preamble = content[:idx] + '/*auto_generator*/\n'
        else:
            idx = content.find('const char ')
            if idx != -1:
                preamble = content[:idx]
            else:
                preamble = content
        # Postamble: everything from /*end_auto_generator*/ onward
        end_idx = content.find('/*end_auto_generator*/')
        if end_idx != -1:
            postamble = content[end_idx:]
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

        out.write(postamble)

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
