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

## Updates
2023.2 Modified by Longshen:
- Some students are not shown in the final allocation results. Solved after adding "completeness term" in fitness function.
- There are usually groups with undesired size. Solved after adding group size penalty term to fitness function.
- (Not done yet) There are too many common topics. Can consider the similarity of topic interest inside the fitness function.
