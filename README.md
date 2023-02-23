# Group Forming Script
This code is made to combine smaller groups into bigger groups according to some objective functions.
The code uses a genetic algorithm to find the optimal groups that maximize the reward (from the objective functions).

This code is working, but has not been refactored for general purposes. Please let me know if you find this code useful and would like me to assist you in using the code or refactoring the code.



## Steps to run
Combine subgroups into groups:
- Prepare the subgroups in the form of json, like `subgroups.json`. The topics indicate how much the subgroup is interested in pursuing the topic, while the skills describe how proficient are the members of the subgroup in those skills. The off-or-on describes the preffered working scheme: `offline (0)`, `hybrid (1)`, or `online (2)`.
- Set the `config.json` to your needs. See the config explanation below.
- Use `form_group.py` to combine the subgroups.


## Config explanation
| key | description |
| --------- | ----- |
| min_score | Minimum score for **each member** to be considered in the reward. Skills that have scores below the min_score will have a reward of 0. |
| max_score | Maximum score of the **combined group** to be considered in the reward. For example, if the combined group has an aggregated score of 10 for a particular skill but the max_score is 9, then the reward for that skill is capped to 9. |
| agg | Aggregation method to be used when calculating the reward of the combined group. |
| weight | Weight for each aspects when calculating the final reward. |
| work_scheme_diff | Tolerance of working scheme difference when calculating the reward. |


## Post-process
After you have run the code, the optimal groupings will be generated based on the `--output_path` argument, which by default is set to `groups.json`. Then, run `json2csv.py` to convert the result from a JSON format into a CSV file.

## Workflow
Basically, the genetic algorithm method works as follows:

1. Accept a population (list of chromosomes). 
2. Create new chromosomes by mating (mixing) some chromosomes and mutating 
the chromosome. 
3. Evaluate the population based on a fitness function (higher better).
Keep the best k chromosomes and discard the rest.

Before optimization, subgroups are separated into two parts: fixed and mutating. 
This is unnecessary in some cases where max_subgroup_members <= max_group_members / 2. You can 
change the variable fix_some on line 37 into False. 

The data representation for the subgroup forming is as follows:
A chromosome is the mapping of the group index for each subgroup in the 
mutating list + dummy (as you don't have a fixed list, the mutating list 
== subgroup list). Dummies are subgroups with 0 members. Dummies are used 
to give more flexibility (i.e., a class of 120 students can be separated 
into 20-24 groups that have 5-6 members). The number of dummies is 
automatically generated on line 155. Dummies will not appear in the final 
prediction, it will just help in allowing more possible configurations.
A population is a list of chromosomes (possible group configurations). We 
only need the best chromosome, but keeping top k helps during the 
optimization to have enough pool of chromosomes to generate new possible 
configurations.
As the chromosome represents the group index, it has to follow certain 
constraints:
All numbers between 0 to {group_size - 1} need to appear in the chromosome 
(we don't want an empty group without any subgroups allocated to it).
Total group members (aggregated from the subgroups within the group) must 
be between the minimum and maximum group members (in your case, 5 to 6).
As the condition for the chromosome is very constraining, I only allow 
swapping mutations (which means swapping which subgroups go into which 
group) and I initialized the population using my own method instead of 
letting the library initialize it randomly. You can imagine if we generate 
random numbers, the chance it produces populations with valid chromosomes 
is quite small. Currently, there are two initialization methods that will 
generate k initial chromosomes (the variable name is actually sol_per_pop 
instead of k).

The first method works by first shuffling the subgroups in the mutation 
list, then filling the group sequentially. The loop on line 189 will add 
as many subgroups as possible to the current group, and the condition on 
line 192 checks whether it's still possible to add the next subgroup or 
not. If this results in the current group having less than the minimum 
group members, the block on line 201 will beg from other groups that have 
maximum group members to give their subgroup who has only 1 member 
(variable members_1) to the current group. I do this because I find it 
easier to fill the gaps with subgroups that only have 1 member. Then, it 
will check the fitness of the current chromosome on line 214 and add it to 
the population if it's a good chromosome. Notice that this is an infinite 
loop (because as I said, getting a good chromosome that suffices the 
constraint is not easy). Each time you get a good chromosome, it will 
print a dot. You should expect k dots printed on the terminal when you 
successfully generate a valid population.

The second method is actually more straightforward but has more magic 
numbers. First, you need to assume how many of the subgroups in the 
mutating list need to be added to the subgroups from the fixed list 
(num_rep_fix in line 221) and how many subgroups it takes to make a new 
group (num_rep_mut in line 223), then if the random group list we created 
is still shorter than the number of chromosomes, it will add more group 
index for the later part. I think the else block is buggy as the 
random.sample function should accept two arguments instead of one. Then it 
will shuffle the group ids and check the fitness of the chromosome, 
similar to the other method.

Alternatively, you can also create your own initialization method. As long 
as you understand the data representation (chromosome and population), you 
are in a good shape to create your own initialization method.

## Updates

2023.2 Modified by Longshen:
- Some students are not shown in the final allocation results. Solved after adding "completeness term" in fitness function.
- There are usually groups with undesired size. Solved after adding group size penalty term to fitness function.
- (Not done yet) There are too many common topics. Can consider the similarity of topic interest inside the fitness function.
