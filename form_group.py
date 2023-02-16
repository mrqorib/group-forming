'''
Merge subgroups to bigger groups.
'''

import argparse
import math
import json
import random

import pygad


def main(args):
    with open(args.config) as f:
        config = json.load(f)  # config
    with open(args.subgroups) as f:
        data = json.load(f)  # subgroup data

    # Set some hyperparameters
    num_students = [len(v['id']) for _, v in data.items()]  # student that is included in all submitted questionnaires
    # NOTE: we need ensuring all students has been added to the subgroup results before proceeding.
    num_groups = int(math.floor(sum(num_students) / float(args.min_member)))  # upper bound of number of final groups
    num_groups = max(num_groups, args.max_group or -1)  # cap to max_group if set
    min_groups = int(math.ceil(sum(num_students) / float(args.max_member)))  # lower bound of number of final groups
    print('Optimizing to {} groups.'.format(num_groups))

    # We only optimize subgroups that have members less or equals to half of the max (<=3)
    fix_some = True
    fixed_groups = []  # a list of groups (json items)
    unfixed_groups = []  # a list of groups (json items)
    for k, v in data.items():
        v['ori_index'] = k
        if fix_some and (len(v['id']) > args.max_member / 2.0):
            fixed_groups.append(v)
        else:
            unfixed_groups.append(v)
    with open('../misc/fixed.json', 'w', encoding='utf-8') as f:
        json.dump(fixed_groups, f, indent=2)
    with open('../misc/mutating.json', 'w', encoding='utf-8') as f:
        json.dump(unfixed_groups, f, indent=2)
    fixed_num = len(fixed_groups)
    unfixed_num = len(unfixed_groups)
    print(
        '{} out of {} subgroups has more than {} members (more than half of max members), will not be optimized'.format(
            fixed_num, len(data), args.max_member / 2.0))

    def merge_group(subgroups, score_only=True, verbose=False):
        '''
        Convert the format of one final group
        from a list of student info
        to a single dict
        And also compute fitness score
        '''

        # print(subgroups)
        # exit(10)
        num_mem = sum([len(s['id']) for s in subgroups])
        if num_mem < args.min_member or num_mem > args.max_member:
            if score_only == True: # still solving
                return -99
            else:
                # print(subgroups)
                if verbose == True:
                    print('WARNING: Unfilled group: {}'.format(num_mem)) # when final output
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
        dic_work_form = {
            "Strictly online": 2,
            "Either is fine": 1,
            "Prefer on-site": 0,
        }
        comb_work = [dic_work_form[s["off-or-on"]] for s in subgroups]
        # print(comb_work)
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
                topic_val = int(topic_val)
                # print(topic, topic_val)
                if topic_val >= config['topics']['interest']:  # Longshen changed > to >=
                    comb_topics['interest'][topic] = True
                    if not score_only and topic_val == config['topics']['max_score']:
                        merged_group['topics']['most_interested'].append(topic)
                if topic not in comb_topics:
                    comb_topics['values'][topic] = []
                comb_topics['values'][topic].append(topic_val)

        skill_score = 0
        for skill_name, skill_conf in config['skills'].items():
            skill_val = [max(int(s) - skill_conf['min'], 0) for s in comb_skills[skill_name]]
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

        # Consider the smallest topic interest difference on a certain topic
        min_topic_diff = None  # min value of interest level difference for a same topic
        for topic, topic_val in comb_topics['values'].items():
            if topic in comb_topics['interest']:
                cur_diff = max(topic_val) - min(topic_val)
                if min_topic_diff is None or cur_diff < min_topic_diff:
                    min_topic_diff = cur_diff
                if not score_only:
                    merged_group['topics']['common'].append((topic, cur_diff))
        if min_topic_diff is not None:
            topic_score = config['topics']['max_score'] - min_topic_diff
            score += topic_score * config['topics']['weight']

        # If any subgroup dislike the most interested topics, add penalty

        # We need at least one person has certain level of programming skill
        max_prog = max([int(i) for i in comb_skills['prog']])
        if max_prog < config['skills']['prog']['min']:  # Longshen: original is <=
            score = 0
        elif min_topic_diff is None:
            score = 0

        # If group size undesired, add penalty.
        group_size = len(merged_group['id'])
        if 5 <= group_size <= 6:
            group_size_penalty = 0
        else:
            group_size_penalty = -1000
        score += group_size_penalty

        if score_only:
            return score
        else:
            merged_group['skills'] = comb_skills
            merged_group['topics']['most_interested'] = list(set(merged_group['topics']['most_interested']))
            merged_group['topics']['common'] = [t[0] for t in
                                                sorted(merged_group['topics']['common'], key=lambda x: x[1])]
            return score, merged_group

    def parse_solution(solution):
        '''
        Decode solution to a list of groups.

        :param solution: raw solution, in ??? form
        :return: a list of decoded groups
        '''
        temp_groups = [[] for _ in range(num_groups)]

        # adding the fixed subgroups first
        for sub_idx, sub in enumerate(fixed_groups):
            temp_groups[sub_idx].append(sub)

        # adding the rest of subgroups
        for sub_idx, sol in enumerate(solution):
            # no need to add the dummy
            if sub_idx >= unfixed_num:
                break
            if sol < len(temp_groups):
                t = unfixed_groups[sub_idx]
                temp_groups[sol].append(t)

        return temp_groups

    def fitness_func(solution, indexes=None):
        '''
        Compute goodness of solution

        :param solution:
        :param indexes:
        :return:
        '''
        temp_groups = parse_solution(solution)
        # print(len(temp_groups), temp_groups[2])
        # exit(10)
        scores = []
        merged_groups = []
        for subgroup in temp_groups:
            if len(subgroup) > 0:
                score, merged_group = merge_group(subgroup, score_only=False)
                scores.append(score)
                merged_groups.append(merged_group)
        cnt = count_stu_num(merged_groups)
        # print('cnt = ', cnt)
        # exit(10)

        # If any student are not allocated, give penalty.
        if cnt < config['total_students']:
            ret = sum(scores) - 1000
        else:
            ret = sum(scores)
        return ret

    def count_stu_num(groups):
        '''
        Count allocated student inside the merged groups
        '''
        cnt = 0
        for group in groups:
            cnt += len(group['id'])
        return cnt

    ### Start the genetic algorithm optimization ###
    fitness_function = fitness_func

    # Define some hyperparameters
    num_generations = 2000  # Loop for 500 iterations
    num_parents_mating = 10  # Select this num of solutions from parent to generate next solution
    sol_per_pop = 10  # Num of solutions within each population
    num_dummy = min(  # Create some empty groups for flexibility
        (num_groups - fixed_num) * (args.max_member - 1) + fixed_num * 2,
        int(round(min_groups * args.dummy_ratio))
    )
    num_genes = unfixed_num + num_dummy  # number of unfixed groups
    print('Using {} number of genes, with {} are dummies'.format(num_genes, num_dummy))
    gene_type = int
    parent_selection_type = "sss"  # steady-state selection
    keep_parents = -1  # keep all parents in next population
    crossover_type = "scattered"  # type of crossover operation
    mutation_type = "swap"  # type of mutation operation
    mutation_percent_genes = 10

    # For 2nd init method
    # init_range_low = 0
    # init_range_high = num_groups - 1

    ### prepare initial population ###
    print('Initializing population')
    populations = []
    num_valid_pop = 0

    '''
    Population: a list of solution
    Chromosome: solution, represent a grouping method, is a list of subgroup id, e.g.
        [3 2 2 1 7 7 0 0 7 3 3 2 2 1 7 7 0 0 7 3]
        The position of each integer represent the original subgroup id
        The value of each integer represent the allocated group's id of that subgroup. 
    Gene: unfixed groups 
    '''

    if args.init_method == 1:
        while len(populations) < sol_per_pop:
            # Generate a solution (chromosome)
            group_members = {}

            # This is a strange initialization. All gene (subgroup id) on the chromosome is initialized to "num_groups"
            chrom = [num_groups] * num_genes

            ids_and_sizes = [(id, len(info['id'])) for id, info in
                             enumerate(unfixed_groups)]  # ids and sizes of groups to be mutated
            random.shuffle(ids_and_sizes)
            new_group_id = 0
            cur_group_size = 0 if fixed_num == 0 else len(fixed_groups[0]['id'])
            members_1 = set([m[0] for m in ids_and_sizes if m[1] == 1])  # 1-member group ids
            for i, (subgroup_id, subgroup_size) in enumerate(ids_and_sizes):
                cur_group_size += subgroup_size
                chrom[subgroup_id] = new_group_id
                if i < len(ids_and_sizes) - 1 and \
                        cur_group_size + ids_and_sizes[i + 1][1] > args.max_member:
                    group_members[new_group_id] = cur_group_size
                    new_group_id += 1
                    if new_group_id < fixed_num:
                        cur_group_size = len(fixed_groups[new_group_id]['id'])
                    else:
                        cur_group_size = 0

            if cur_group_size < args.min_member:
                remain = args.min_member - cur_group_size
                pool = []
                for m_id, g_id in enumerate(chrom):
                    if (g_id in group_members) and group_members[g_id] == args.max_member \
                            and (m_id in members_1):
                        pool.append(m_id)
                if remain <= len(pool):  # If can change, move 1-member subgroup to the last unfilled group
                    change = random.sample(pool, remain)
                    for subgroup_id in change:
                        # print('taking {} from {}'.format(m_id, chrom[m_id]))
                        chrom[subgroup_id] = new_group_id
                        cur_group_size += 1
                    group_members[new_group_id] = cur_group_size

            score = fitness_func(chrom)
            # print(score)
            if score > 0 and new_group_id <= num_groups:
                num_valid_pop += 1
                populations.append(chrom)
                print('.', end='')
    else:
        raise NotImplementedError
    print()

    ga_instance = pygad.GA(
        num_generations=num_generations,
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
            t1 = merge_group(subgroup, score_only=False, verbose=True)
            # print(t1)
            t2 = t1[1]
            final_groups.append(t2)
    # groups = [merge_group(g, score_only=False)[1] for g in groups]
    # print("Parameters of the best solution : {solution}".format(solution=solution))
    print("Fitness value of the best solution = {solution_fitness}".format(solution_fitness=solution_fitness))
    with open(args.output_path, 'w', encoding='utf-8') as out:
        json.dump(final_groups, out, indent=2)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subgroups', default='../input/subgroups.json', help='path to the json file containing all subgroups')
    parser.add_argument('--min_member', type=int, default=5, help="minimum members in a group")
    parser.add_argument('--max_member', type=int, default=6, help="maximum members in a group")
    parser.add_argument('--min_group', type=int, default=31, help="minimum number of groups")
    parser.add_argument('--max_group', type=int, default=38, help="maximum number of groups")
    parser.add_argument('--init_method', type=int, default=1, help="maximum number of groups")
    parser.add_argument('--dummy_ratio', type=float, default=2, help="percentage of additional dummy subgroups")
    parser.add_argument('--config', default='../configs/4248.json', help='path to the config file')
    parser.add_argument('--output_path', default='../output/group_allocation.json', help='path to the output file')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    main(args)
