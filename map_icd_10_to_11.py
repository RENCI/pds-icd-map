import pandas as pd
import sys
import os
import json


if len(sys.argv) <= 1:
    print("Usage: python map_icd_10_to_11.py output_file_name.json")
    exit(1)

output_file_name = sys.argv[1].strip()
if not output_file_name.endswith('.json'):
    print("The pass in output file name argument must have an extension .json")
    exit(1)

input_map_file = os.path.join('data', 'input', '10To11Map.csv')
output_map_file = os.path.join('data', 'output', output_file_name)

df = pd.read_csv(input_map_file, header=0)
df = df[df['10ClassKind'] == 'category']
df = df[df['icd11Code'].notnull()]
df = df.drop(columns=['10ClassKind', '11ClassKind'])
df.set_index("icd10Code", inplace=True)
icd11_code_series = df['icd11Code']
data_map_dict = icd11_code_series.to_dict()

input_map_supl_file = os.path.join('data', 'input', '10To11MapSupl.json')
with open(input_map_supl_file) as supl_json_file:
    supl_data = json.load(supl_json_file)
    data_map_dict.update(supl_data)

with open(output_map_file, 'w') as fp:
    json.dump(data_map_dict, fp)
