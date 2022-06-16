import argparse
import math
import json
import random

import pygad


def main(args):
    with open(args.config) as f:
        config = json.load(f)
    with open(args.subgroups) as f:
        data = json.load(f)
    
    num_students = [len(v['id']) for _, v in data.items()]

    num_groups = int(math.floor(sum(num_students) / float(args.min_member)))
    num_groups = max(num_groups, args.max_group or -1) # cap to max_group if set
    min_groups = int(math.ceil(sum(num_students) / float(args.max_member)))
    print('Optimizing to {} groups.'.format(num_groups))

    fixed = []
    mutating = []
    fix_some = True
    # data = {k: v for k, v in sorted(data.items(), reverse=True, key=lambda item: len(item[1]['id']))}
    for k, v in data.items():
        v['ori_index'] = k
        # do not optimize subgroups that have members more than half of the max
        if fix_some and (len(v['id']) > args.max_member / 2.0):
            fixed.append(v)
        else:
            mutating.append(v)
    with open('fixed.json', 'w', encoding='utf-8') as f:
        json.dump(fixed, f, indent=2)
    with open('mutating.json', 'w', encoding='utf-8') as f:
        json.dump(mutating, f, indent=2)
    fixed_num = len(fixed)
    mut_num = len(mutating)
    print('{} out of {} subgroups has more than {} members'.format(fixed_num, len(data), \
        args.max_member / 2.0) + '(more than half of max members), will not be optimized')
    
    def merge_group(subgroups, score_only=True):
        num_mem = sum([len(s['id']) for s in subgroups])
        if num_mem < args.min_member or num_mem > args.max_member:
            return -99
        if not score_only:
            merged_group = {
                'name': [],
                'id': [],
                'study': [],
                'topics': {
                    'most_interested': [],
                    'common': [],
                },
            }
            for s in subgroups:
                for key in ['name', 'id', 'study']:
                    merged_group[key].extend(s[key])
        comb_work = [s["off-or-on"] for s in subgroups]
        score = 1 if (max(comb_work) - min(comb_work)) <= config['work_scheme_diff'] else 0
        comb_skills = {}
        comb_topics = {
            'interest': {},
            'values': {}
        }
        for subg in subgroups:
            for skill, skill_val in subg['skills'].items():
                if skill not in comb_skills:
                    comb_skills[skill] = []
                comb_skills[skill].extend(skill_val)
            for topic, topic_val in subg['topics'].items():
                if topic_val > config['topics']['interest']:
                    comb_topics['interest'][topic] = True
                    if not score_only and topic_val == config['topics']['max_score']:
                        merged_group['topics']['most_interested'].append(topic)
                if topic not in comb_topics:
                    comb_topics['values'][topic] = []
                comb_topics['values'][topic].append(topic_val)

        skill_score = 0
        for skill_name, skill_conf in config['skills'].items():
            skill_val = [max(s - skill_conf['min'], 0) for s in comb_skills[skill_name]]
            if skill_conf['agg'] == 'sum':
                cur_score = sum(skill_val)
            elif skill_conf['agg'] == 'max':
                cur_score = max(skill_val)
            else:
                raise NotImplementedError
            if 'max' in skill_conf:
                cur_score = min(cur_score, skill_conf['max'])
            skill_score += cur_score * skill_conf['weight']
        score += skill_score
        
        min_topic_diff = None
        for topic, topic_val in comb_topics['values'].items():
            if topic in comb_topics['interest']:
                cur_diff = max(topic_val) - min(topic_val)
                if min_topic_diff is None or cur_diff < min_topic_diff:
                    min_topic_diff = cur_diff
                if not score_only:
                    merged_group['topics']['common'].append((topic, cur_diff))
        
        # topic_val = [max(v) - min(v) for _, v in comb_topics.items()]
        if min_topic_diff is not None:
            topic_score = config['topics']['max_score'] - min_topic_diff
            score += topic_score * config['topics']['weight']

        max_prog = max(comb_skills['prog'])
        if max_prog <= config['skills']['prog']['min']:
            score = 0
        elif min_topic_diff is None:
            score = 0

        if score_only:
            return score
        else:
            merged_group['skills'] = comb_skills
            merged_group['topics']['most_interested'] = list(set(merged_group['topics']['most_interested']))
            merged_group['topics']['common'] = [t[0] for t in sorted(merged_group['topics']['common'], key=lambda x: x[1])]
            return score, merged_group


    def parse_solution(solution):
        temp_groups = [[] for _ in range(num_groups)]
        # adding the fixed subgroups first
        for sub_idx, sub in enumerate(fixed):
            temp_groups[sub_idx].append(sub)
        # adding the rest of subgroups
        for sub_idx, sol in enumerate(solution):
            # no need to add the dummy
            if sub_idx >= mut_num:
                break
            temp_groups[sol].append(mutating[sub_idx])

        return temp_groups


    def fitness_func(solution, indexes=None):
        temp_groups = parse_solution(solution)
        scores = []
        for subgroup in temp_groups:
            if len(subgroup) > 0:
                scores.append(merge_group(subgroup))

        return sum(scores)


    ### Start the genetic algorithm optimization ###
    fitness_function = fitness_func

    num_generations = 500
    num_parents_mating = 10

    sol_per_pop = 10
    num_dummy = min((num_groups - fixed_num) * (args.max_member - 1) + fixed_num * 2,
                    int(round(min_groups * args.dummy_ratio))
                    )
    num_genes = mut_num + num_dummy
    print('Using {} number of genes, with {} are dummies'.format(num_genes, num_dummy))
    gene_type = int

    init_range_low = 0
    init_range_high = num_groups - 1

    parent_selection_type = "sss"
    keep_parents = -1

    crossover_type = "scattered"

    mutation_type = "swap"
    mutation_percent_genes = 10

    ### prepare initial population ###
    print('Initializing population')
    populations = []
    num_valid_pop = 0
    num_rep_fix = 2
    num_rep_mut = 3
    num_iter = 0
    if args.init_method == 1:  
        while len(populations) < sol_per_pop:
            group_members = {}
            chrom = [num_groups] * num_genes
            mut_ids = [(i, len(m['id'])) for i, m in enumerate(mutating)]
            random.shuffle(mut_ids)
            group_id = 0
            cur_group_size = len(fixed[0]['id']) # args.max_member + 1
            members_1 = set([m[0] for m in mut_ids if m[1] == 1])
            for l_i, (m_id, m_len) in enumerate(mut_ids):
                cur_group_size += m_len
                chrom[m_id] = group_id
                if l_i < len(mut_ids) -1 and \
                    cur_group_size + mut_ids[l_i + 1][1] > args.max_member:
                    group_members[group_id] = cur_group_size
                    group_id += 1
                    if group_id < fixed_num:
                        cur_group_size = len(fixed[group_id]['id'])
                    else:
                        cur_group_size = 0
            
            if cur_group_size < args.min_member:
                remain = args.min_member - cur_group_size
                pool = []
                for m_id, g_id in enumerate(chrom):
                    if (g_id in group_members) and group_members[g_id] == args.max_member \
                        and (m_id in members_1):
                        pool.append(m_id)
                change = random.sample(pool, remain)
                for m_id in change:
                    # print('taking {} from {}'.format(m_id, chrom[m_id]))
                    chrom[m_id] = group_id
                    cur_group_size += 1
                group_members[group_id] = cur_group_size
            if fitness_func(chrom) > 0 and group_id <= num_groups:
                num_valid_pop += 1
                populations.append(chrom)
                print('.', end='')
    elif args.init_method == 2:
        while len(populations) < sol_per_pop:
            chrom = []
            for _fix_i in range(num_rep_fix):
                chrom += list(range(0, fixed_num))
            for _mut_i in range(num_rep_mut):
                chrom += list(range(fixed_num, num_groups))
            # chrom += random.sample(list(range(fixed_num)), round(random.random() * fixed_num))
            random_num = num_genes - len(chrom)
            if random_num > 0:
                # print('Adding {} more genes'.format(random_num))
                add_chrom = []
                num_rep = random_num // (args.max_member - num_rep_mut)
                for _ii in range(num_rep + 1):
                    add_chrom += list(range(fixed_num, num_groups))
                chrom += random.sample(add_chrom, random_num)
            else:
                # print('Sampling the genes from {} to {}'.format(len(chrom), num_genes))
                chrom = random.sample(num_genes)
            random.shuffle(chrom)
            num_iter += 1
            if fitness_func(chrom) > 0:
                num_valid_pop += 1
                populations.append(chrom)
                print('.', end='')
    else:
        raise NotImplementedError
    print()
    
    ga_instance = pygad.GA(num_generations=num_generations,
                       num_parents_mating=num_parents_mating,
                       fitness_func=fitness_function,
                       initial_population=populations,
                       gene_type=gene_type,
                       parent_selection_type=parent_selection_type,
                       keep_parents=keep_parents,
                       crossover_type=crossover_type,
                       mutation_type=mutation_type,
                       mutation_percent_genes=mutation_percent_genes,
                       )
    print('Optimizing...')
    ga_instance.run()
    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    print('Finished. Constructing the groups...')
    print(solution)
    groups = parse_solution(solution)
    final_groups = []
    for subgroup in groups:
        if len(subgroup) > 0:
            final_groups.append(merge_group(subgroup, score_only=False)[1])
    # groups = [merge_group(g, score_only=False)[1] for g in groups]
    # print("Parameters of the best solution : {solution}".format(solution=solution))
    print("Fitness value of the best solution = {solution_fitness}".format(solution_fitness=solution_fitness))
    with open(args.output_path, 'w', encoding='utf-8') as out:
        json.dump(final_groups, out, indent=2)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subgroups', help='path to the json file containing all subgroups')
    parser.add_argument('--min_member', type=int, default=4, help="minimum members in a group")
    parser.add_argument('--max_member', type=int, default=5, help="maximum members in a group")
    parser.add_argument('--min_group', type=int, default=None, help="minimum number of groups")
    parser.add_argument('--max_group', type=int, default=None, help="maximum number of groups")
    parser.add_argument('--init_method', type=int, default=1, help="maximum number of groups")
    parser.add_argument('--dummy_ratio', type=float, default=2, help="percentage of additional dummy subgroups")
    parser.add_argument('--config', default='config.json', help='path to the config file')
    parser.add_argument('--output_path', default='groups.json', help='path to the output file')
    return parser.parse_args()

if __name__ == "__main__":
    args = get_arguments()
    main(args)