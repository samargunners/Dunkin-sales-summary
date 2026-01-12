"""Test normalize_location function"""
import sys
sys.path.insert(0, 'scripts')
from parse_transposed_format import normalize_location, PC_TO_STORE

test = '362913 - 900 Eisenhower Blvd'
result = normalize_location(test)
print(f'Input: {test}')
print(f'Result: {result}')
print(f'In PC_TO_STORE: {result in PC_TO_STORE if result else False}')
if result:
    print(f'Store name: {PC_TO_STORE.get(result, "NOT FOUND")}')

