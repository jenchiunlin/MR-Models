import os
import sys
import pandas as pd
from datasets import load_dataset

def list_subdirs(path_dir):
    return [d for d in os.listdir(path_dir) if os.path.isdir(os.path.join(path_dir, d))]

def ensure_dirs(path):
    os.makedirs(path, exist_ok=True)

def make_question(d):
    def remove_period(s):
        if s[-1] == '。' or s[-1] == '.':
            return s[:-1]
        return s
    
    idx = int(d['id'].split('-')[-1])
    q = d['question']
    a = remove_period(d['A'])
    b = remove_period(d['B'])
    c = remove_period(d['C'])
    d = remove_period(d['D'])
    return f'{idx+1}. {q}(A){a}(B){b}(C){c}(D){d}。'

path_input = sys.argv[1]
prefix = sys.argv[2]
for path_dir in list_subdirs(path_input):
    if not path_dir.startswith(prefix):
        continue
    dataset = load_dataset(path_input, path_dir, split='test')
    subject =  dataset['subject'][0]
    data = {
        'content.A': dataset['answer'],
        'content.Q': [make_question(d) for d in dataset],
    }
    path_subject = os.path.join('subjects', subject)
    ensure_dirs(path_subject)
    path_csv = os.path.join(path_subject, 'data.csv')
    pd.DataFrame(data).to_csv(path_csv, encoding='utf-8')
