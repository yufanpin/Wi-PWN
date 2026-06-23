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
from os.path import join, isdir

def generate_data_h(input_dir, output_path):
    # Collect files matching auto_generate.exe behavior:
    #   - .html and .css from root level only
    #   - .js from js/ subdirectory only
    # This matches the original Node.js auto_generate.exe which does:
    #   fs.readdir(output/html) -> .html + .css (root level)
    #   fs.readdir(output/html/js) -> .js (js/ subdir)
    files = []
    root_dir = input_dir
    js_dir = join(input_dir, 'js')
    
    # Root level: .html and .css
    if isdir(root_dir):
        for f in sorted(os.listdir(root_dir)):
            full = join(root_dir, f)
            if not os.path.isfile(full):
                continue
            ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
            if ext in ('html', 'css'):
                files.append(full)
    
    # js/ subdirectory: .js
    if isdir(js_dir):
        for f in sorted(os.listdir(js_dir)):
            full = join(js_dir, f)
            if not os.path.isfile(full):
                continue
            ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
            if ext == 'js':
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
            # Convert filename to C identifier matching auto_generate.exe convention:
            #   extension = UPPERCASE, filename = lowercase
            #   e.g. main.css -> data_main_CSS, 404.html -> data_404_HTML
            parts = fname.rsplit('.', 1)
            if len(parts) == 2:
                file_part = parts[0].lower()
                ext_part = parts[1].upper()
            else:
                file_part = parts[0].lower()
                ext_part = ''
            c_name = f'data_{file_part}_{ext_part}'

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
