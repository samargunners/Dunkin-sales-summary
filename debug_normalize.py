"""Debug normalize_location"""
import sys
import re
sys.path.insert(0, 'scripts')
from parse_transposed_format import LOC_TO_PC, PC_TO_STORE

test = '362913 - 900 Eisenhower Blvd'
print(f'Testing: "{test}"')
print(f'\nLOC_TO_PC keys:')
for key in LOC_TO_PC.keys():
    print(f'  "{key}"')
    if '362913' in key:
        print(f'    -> Matches! PC: {LOC_TO_PC[key]}')

print(f'\nTrying exact match: {test in LOC_TO_PC}')

print(f'\nTrying partial match:')
for key, pc in LOC_TO_PC.items():
    if key in test or test in key:
        print(f'  "{key}" matches "{test}" -> PC: {pc}')

print(f'\nTrying regex extraction:')
pc_match = re.search(r'(\d{6})', test)
if pc_match:
    pc_number = pc_match.group(1)
    print(f'  Extracted PC: {pc_number}')
    print(f'  In PC_TO_STORE: {pc_number in PC_TO_STORE}')
    if pc_number in PC_TO_STORE:
        print(f'  Store name: {PC_TO_STORE[pc_number]}')

