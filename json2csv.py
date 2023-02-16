import json
import sys


def main():
    max_members = 5
    with open(sys.argv[1], encoding='utf-8') as f:
        data = json.load(f)
    id_name_list = ['name', 'id']
    topic_map = {
        'Communication': 'How to communicate effectively',
        'Marketing': 'Sell your first product fast',
        'Business': 'Grow your business like a tree',
    }
    header = ['gid']
    for i in range(max_members):
        for col in id_name_list:
            header.append('{}_{}'.format(col, i + 1))
    header.append('common_topics')

    content = []
    for g_id, group in enumerate(data):
        row = [g_id + 1]
        for i in range(max_members):
            for col in id_name_list:
                if i < len(group[col]):
                    row.append(group[col][i])
                else:
                    row.append('')
        common_topics = [topic_map[t] for t in group["topics"]["common"]]
        row.append('; '.join(common_topics))
        content.append(row)

    try:
        import pandas as pd
        df = pd.DataFrame(content, columns=header)
        df.to_csv(sys.argv[2], index=False)
    except ImportError:
        with open(sys.argv[2], 'w', encoding='utf-8') as out:
            for row in header + content:
                out.write(', '.join(row))


if __name__ == "__main__":
    main()