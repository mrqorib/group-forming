import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from utils import save_json, read_json, print_json

def _main():
    pass
    # check_completeness()
    convert_to_csv()
    # check_dataset_distribution()

def _procedures():
    check_completeness()
    convert_to_csv()


def check_dataset_distribution():
    data = read_json('../output/group_allocation.json')

    res = {
        "LUN": 0,
        "Emoji": 0,
        "ConceptNet": 0,
        "Dialogue": 0,
        "SciCite": 0,
        "IWSLT": 0,
        "SQuAD": 0,
        "SNLI": 0
    }
    for team in data:
        datasets = team['topics']['most_interested']
        score = 1 / len(datasets)
        for dataset in datasets:
            res[dataset] += score
    print_json(res)

    plt.figure(figsize=[5,3])
    plt.xticks(rotation=45)
    lists = sorted(res.items())
    x, y = zip(*lists)
    plt.bar(x, y)
    plt.tight_layout()
    plt.savefig('res.png')


def convert_to_csv():
    '''
    Convert allocation results to csv, format as below:
    team_id    p1_name p1_id   p2_name ... p6_id   most_interested_topics   common_topics
    1
    2
    3
    ...
    :return:
    '''
    data = read_json('../output/group_allocation.json')
    team_id = 0
    res = []
    for group in data:
        team_id += 1
        team_size = len(group['name'])
        names = group['name']
        ids = group['id']
        for i in range(6-team_size):
            names.append('')
            ids.append('')
        assert len(names) == 6
        p1_name = names[0]
        p2_name = names[1]
        p3_name = names[2]
        p4_name = names[3]
        p5_name = names[4]
        p6_name = names[5]
        p1_id = ids[0]
        p2_id = ids[1]
        p3_id = ids[2]
        p4_id = ids[3]
        p5_id = ids[4]
        p6_id = ids[5]
        most_interested_topics = group['topics']['most_interested']
        common_topics = group['topics']['common']
        res.append({
            'team_id': team_id,
            'p1_name': p1_name,
            'p1_id': p1_id,
            'p2_name': p2_name,
            'p2_id': p2_id,
            'p3_name': p3_name,
            'p3_id': p3_id,
            'p4_name': p4_name,
            'p4_id': p4_id,
            'p5_name': p5_name,
            'p5_id': p5_id,
            'p6_name': p6_name,
            'p6_id': p6_id,
            'most_interested_topics': most_interested_topics,
            'common_topics': common_topics,
        })
    df = pd.DataFrame(res)
    print(df.head())
    df.to_csv('../output/group_allocation.csv', index=False)

def check_completeness():
    '''
    Check does all students are included in the allocation results
    '''
    data = read_json('../output/group_allocation.json')
    print('{} groups in total.'.format(len(data)))
    cnt = 0
    for group in data:
        cnt += len(group['id'])
    print('{} students are allocated.'.format(cnt))

    # Read the full student list
    df = pd.read_csv('../raw/all_student_clean_20210130.csv')
    stu_total = set(list(df['SIS ID']))

    # Get all allocated student
    stu_alloc = set()
    for group in data:
        stu_alloc.update(group['id'])

    for id in stu_total:
        if id not in stu_alloc:
            print(id)


if __name__ == '__main__':
    _main()
