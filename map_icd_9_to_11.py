import sys
import os
import json


if len(sys.argv) <= 3:
    print("Usage: python map_icd_9_to_11.py icd_9_to_10_map.json icd_10_to_11_map.json icd_9_to_11_map.json")
    exit(1)

input_file_name_1 = sys.argv[1].strip()
input_file_name_2 = sys.argv[2].strip()
output_file_name = sys.argv[3].strip()
if not output_file_name.endswith('.json') or not input_file_name_1.endswith('.json') or \
        not input_file_name_2.endswith('.json'):
    print("The pass in input and output file name arguments must all be json file and have an extension .json")
    exit(1)

input_1_map_file = os.path.join('data', 'output', input_file_name_1)
input_2_map_file = os.path.join('data', 'output', input_file_name_2)
output_map_file = os.path.join('data', 'output', output_file_name)

with open(input_1_map_file) as f:
    input_1_data = json.load(f)

with open(input_2_map_file) as f:
    input_2_data = json.load(f)

data_map_dict = {}
total_invalid = 0
total_valid = 0
for key in input_1_data:
    val = input_1_data[key]
    if val in input_2_data:
        data_map_dict[key] = input_2_data[val]
        total_valid += 1
    else:
        print(val, " icd 10 code is not mapped to icd 11 code, so ", key, " icd 9 code cannot be mapped to icd 11 code")
        total_invalid += 1
print("total number of successfully mapped icd 9 codes: ", total_valid)
print("total number of fail-to-be-mapped icd 9 codes: ", total_invalid)
with open(output_map_file, 'w') as fp:
    json.dump(data_map_dict, fp)
