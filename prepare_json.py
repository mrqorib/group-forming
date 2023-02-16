'''
Convert prepared deduplicated data in csv file to json format
'''

import os
import sys
import json
import pandas as pd

input_path = '../raw/subgroup_preference.csv'
output_path = '../input/subgroups.json'


def _main():
    pass
    convert_csv_to_json()


def _procedures():
    pass


def convert_csv_to_json():
    '''
    Format:
    {
        'sub_id': {
            'name': [],
            'id': [],
            'study': [],
            'skills': {},
            'topics': {},
            'off-or-on': int
        }
    }
    '''
    df = pd.read_csv(input_path)
    data = {}
    for i, row in df.iterrows():
        sub_id = i
        sub_size = 0  # size of subgroup
        names = []
        for j in ['p1_name', 'p2_name', 'p3_name']:
            t = row[j]
            if isinstance(t, str):
                names.append(t)
                sub_size += 1
        ids = []
        study = []
        skills = {}
        skill_term = ['prog', 'dc', 'da', 'ml', 'dl', 'ling', 'writ', 'nlp']
        for term in skill_term:
            skills[term] = []
        all_topics = ['LUN', 'Emoji', 'ConceptNet', 'Dialogue', 'SciCite', 'IWSLT', 'SQuAD', 'SNLI']
        topics = {}
        for j in range(1, sub_size + 1):
            # print(row)
            ids.append(row['p{}_id'.format(j)])
            study.append(row['p{}_program'.format(j)])
            print(i, j, row['p{}_skill'.format(j)])
            skill_scores = row['p{}_skill'.format(j)].split(',')
            for k in range(len(skill_scores)):
                term_score = skill_scores[k]
                skills[skill_term[k]].append(term_score)
        topic_scores = row['dataset'].split(',')
        for j in range(len(all_topics)):
            topics[all_topics[j]] = topic_scores[j]
        off_or_on = row['meet_form']

        data[sub_id] = {
            'name': names,
            'id': ids,
            'study': study,
            'skills': skills,
            'topics': topics,
            'off-or-on': off_or_on,
        }

    save_json(data, output_path)


def read_json(path):
    with open(path, 'r', encoding='utf8') as f:
        data = f.read()
        data = json.loads(data)
    return data


def save_json(data, path, sort=False):
    with open(path, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, indent=4, sort_keys=sort, ensure_ascii=False))


def print_json(data):
    print(json.dumps(data, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    _main()
