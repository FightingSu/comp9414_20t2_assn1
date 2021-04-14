import sys
import re
from cspProblem import Constraint, CSP
from cspConsistency import Search_with_AC_from_CSP
from searchGeneric import AStarSearcher
from itertools import accumulate


'''
due to numbers' comparable nature, the
domains are presented in a 3-digit number
where the hundreds place shows the weekday
the tens place and ones place shows the time

the following four dictionaries are dedicated for
conversion from string to value and vice versa
'''
# for look up value for some weekday
week_dict = dict(zip(
    ['mon', 'tue', 'wed', 'thu', 'fri'],
    [i * 100 for i in range(1, 6)]
))


# for look up value for some daytime
time_dict = dict(zip(
    ['{}am'.format(i) if (i < 12) else '12pm'
     if (i == 12) else '{}pm'.format(i - 12)
        for i in range(9, 18)],
    [i for i in range(9, 18)]
))


# all the working time slot
timeslot_mapping = dict([(week_dict[d] + time_dict[t], d + ' ' + t)
                         for t in time_dict.keys()
                         for d in week_dict.keys()])
reversed_timeslot = dict([(d + ' ' + t, week_dict[d] + time_dict[t])
                          for t in time_dict.keys()
                          for d in week_dict.keys()])


# convert time from 3-digit number to hours
# its useful when it comes to the cost calculation
def convert_to_hours(t):
    return t % 100 + (t - 100) // 100 * 24


''' 
constraints verification functions 

each varify function require two tuples
the 0 position stands for the starting time
and 1 position stands for the ending time
'''


# t1 ends when or before t2 starts
def before(t1: tuple, t2: tuple):
    return t1[1] <= t2[0]


# t1 starts after or when t2 ends
def after(t1: tuple, t2: tuple):
    return t1[0] >= t2[1]


# t1 and t2 are scheduled on the same day
def same_day(t1: tuple, t2: tuple):
    return t1[0] // 100 == t2[0] // 100


# t1 starts exactly when t2 ends
def start_at(t1: tuple, t2: tuple):
    return t2[1] == t1[0]


''' cost computing '''


# compute cost of a task with actual finish time and deadline
def compute_single_cost(deadline: int, actual_time: int, cost: int):
    actual_time = convert_to_hours(actual_time)
    deadline = convert_to_hours(deadline)

    time_gap = actual_time - deadline
    if time_gap <= 0:
        return 0
    else:
        return time_gap * cost


# compute cost from given schedule
def compute_total_cost(schedule: dict, deadlines: dict, costs: dict):
    cost = 0
    for k in schedule:
        cost += compute_single_cost(deadlines[k], schedule[k], costs[k])
    return cost


''' read files '''


# read domains
# it also remove impossible values for domain
# therefore this function is quite long
def read_domain(sz_domain: str, possible_value: set,
                duration: int):
    cost = 0
    deadline = 0
    if 'starts-before' in sz_domain:
        sz_domain = sz_domain.split(' ')[1:]
        if len(sz_domain) == 1:
            sz_domain = sz_domain[0]
            possible_value = [
                v for v in possible_value
                if v % 100 <= time_dict[sz_domain]
            ]
        else:
            sz_domain = ' '.join(sz_domain)
            possible_value = [
                v for v in possible_value
                if v <= reversed_timeslot[sz_domain]
            ]
    elif 'ends-before' in sz_domain:
        sz_domain = sz_domain.split(' ')[1:]
        if len(sz_domain) == 1:
            sz_domain = sz_domain[0]
            possible_value = [
                v for v in possible_value
                if v % 100 + duration <= time_dict[sz_domain]
            ]
        else:
            sz_domain = ' '.join(sz_domain)
            possible_value = [
                v for v in possible_value
                if v + duration <= reversed_timeslot[sz_domain]
            ]
    elif 'starts-after' in sz_domain:
        sz_domain = sz_domain.split(' ')[1:]
        if len(sz_domain) == 1:
            sz_domain = sz_domain[0]
            possible_value = [
                v for v in possible_value
                if v % 100 >= time_dict[sz_domain]
            ]
        else:
            sz_domain = ' '.join(sz_domain)
            possible_value = [
                v for v in possible_value
                if v >= reversed_timeslot[sz_domain]
            ]
    elif 'ends-after' in sz_domain:
        sz_domain = sz_domain.split(' ')[1:]
        if len(sz_domain) == 1:
            sz_domain = sz_domain[0]
            possible_value = [
                v for v in possible_value
                if v % 100 + duration >= time_dict[sz_domain]
            ]
        else:
            sz_domain = ' '.join(sz_domain)
            possible_value = [
                v for v in possible_value
                if v + duration >= reversed_timeslot[sz_domain]
            ]
    elif 'starts-in' in sz_domain:
        sz_domain = ' '.join(sz_domain.split(' ')[1:]).split('-')
        possible_value = [
            v for v in possible_value
            if v >= reversed_timeslot[sz_domain[0]] and
            v <= reversed_timeslot[sz_domain[1]]
        ]
    elif 'ends-in' in sz_domain:
        sz_domain = ' '.join(sz_domain.split(' ')[1:]).split('-')
        possible_value = [
            v for v in possible_value
            if v + duration >= reversed_timeslot[sz_domain[0]] and
            v + duration <= reversed_timeslot[sz_domain[1]]
        ]
    elif sz_domain in week_dict:
        possible_value = [
            v for v in possible_value
            if v // 100 == week_dict[sz_domain] // 100
        ]
    elif sz_domain in time_dict:
        possible_value = [
            v for v in possible_value
            if v % 100 == time_dict[sz_domain] % 100
        ]
    elif 'ends-by' in sz_domain:
        sz_domain = sz_domain.split(' ')[1:]
        cost = int(sz_domain[-1])
        deadline = reversed_timeslot[' '.join(sz_domain[:-1])]

    return possible_value, cost, deadline


# read tasks, constraints and domain from given file
def read_task(filename: str):
    all_constraints = []
    all_domains = {}
    all_tasks = {}
    with open(filename, 'r') as f:
        content = f.read()

        # fit content for regex expression
        content = content + '\n'

        # remove comment and extra spaces
        content = re.sub('\s*#.*\n', '\n', content)
        content = re.sub('[ ]+', ' ', content)
        content = re.sub('\s*\n\s*', '\n', content)
       #  print(content)

        # init tasks
        result = dict(re.findall(
            'task,\s(.*?)\s(.*?)\n', content, re.S
        ))

        #print(result)

        all_tasks = {k: {'duration': int(result[k])} for k in result}

        # find domains for tasks
        for t in all_tasks:
            result = tuple(re.findall(
                'domain,\s{}\s(.*?)\n'.format(t), content, re.S
            ))

            # valid start time. The result of start time + duration
            # must to be in timeslot_mapping
            possible_value = {
                v for v in set(timeslot_mapping.keys())
                if v + all_tasks[t]['duration'] in timeslot_mapping
            }
            task_cost = 0
            soft_deadline = 0
            for r in result:
                possible_value, cost, deadline = \
                    read_domain(r, possible_value,
                                all_tasks[t]['duration'])
                if cost != 0:
                    task_cost = cost
                    soft_deadline = deadline

            # meta-info records the raw information about the
            # domain from text file
            all_tasks[t]['meta-info'] = result

            # if a task have soft deadline, then
            # the cost and deadlline are greater than 0
            all_tasks[t]['cost'] = task_cost
            all_tasks[t]['deadline'] = soft_deadline
            all_domains[t] = {(start, start + all_tasks[t]['duration'])
                              for start in possible_value}

        # load all the constraints
        result = tuple(re.findall(
            'constraint,\s(.*?)\s(.*?)\s(.*?)\n', content, re.S))

        # construct constraints
        for t1, cons_type, t2 in result:
            cons = None
            if cons_type == 'before':
                cons = Constraint((t1, t2), before)
            elif cons_type == 'after':
                cons = Constraint((t1, t2), after)
            elif cons_type == "same-day":
                cons = Constraint((t1, t2), same_day)
            else:
                cons = Constraint((t1, t2), start_at)
            all_constraints.append(cons)

    return all_tasks, all_constraints, all_domains


# search one schedule for one file
def get_one_schedule(filename):
    '''
    tasks keeps meta information: task name, task duration
    domains keeps possible values for tasks
    constraints contains two tasks and one condition
    costs is task_name: cost_per_hour key-value pairs
    '''
    tasks, constraints, domains = read_task(filename)
    deadlines = {k: tasks[k]['deadline'] for k in tasks}
    costs = {k: tasks[k]['cost'] for k in tasks}

    schedule_csp = MyCSP(domains, constraints, tasks)
    searcher = AStarSearcher(Search_with_AC_from_Cost_CSP(schedule_csp))
    searcher.max_display_level = 0
    path = searcher.search()

    if path is None:
        print('No solution')
    else:
        assignments = {k: v.pop()[0] for k, v in path.end().items()}
        for k, v in assignments.items():
            print('{}:{}'.format(k, timeslot_mapping[v]))
        assignments = {k: v + tasks[k]['duration']
                       for k, v in assignments.items()}
        total_cost = compute_total_cost(assignments, deadlines, costs)
        print('cost:{}'.format(total_cost))


# adds costs and deadlines as the class members
class MyCSP(CSP):
    def __init__(self, domains: dict, constraints: Constraint, tasks: dict):
        super().__init__(domains, constraints)
        self.costs = {k: tasks[k]['cost'] for k in tasks}
        self.deadlines = {k: tasks[k]['deadline'] for k in tasks}


class Search_with_AC_from_Cost_CSP(Search_with_AC_from_CSP):
    def __init__(self, csp: CSP):
        super().__init__(csp)
        self.csp = csp
        # sort variables by the earliest starting time
        self.variables = set(sorted(csp.domains, key=lambda t: csp.domains[t]))

    def heuristic(self, node):
        result = [0] + list(accumulate((
            min(node[var])[1] - self.csp.deadlines[var]) * self.csp.costs[var]
            for var in node
            if self.csp.costs[var] != 0 and len(node[var]) > 0))
        return result[-1]


if __name__ == '__main__':
    task_files = sys.argv[1:]
    for i in task_files:
        get_one_schedule(i)
