import pandas as pd
import sys
import os
import json


if len(sys.argv) <= 1:
    print("Usage: python map_icd_9_to_10.py output_file_name.json")
    exit(1)

output_file_name = sys.argv[1].strip()
if not output_file_name.endswith('.json'):
    print("The pass in output file name argument must have an extension .json")
    exit(1)

input_map_file = os.path.join('data', 'input', '9To10Map.csv')
output_map_file = os.path.join('data', 'output', output_file_name)

data_map_dict = pd.read_csv(input_map_file, usecols=[0, 2], index_col=0, header=None, squeeze=True).to_dict()

with open(output_map_file, 'w') as fp:
    json.dump(data_map_dict, fp)
