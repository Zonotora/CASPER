#from scipy.optimize import linprog
#from scheduler.task import TaskBatch
import numpy as np
import math
import pulp as plp


def schedule(task_batch, servers, algorithm, t):
    """
    {
        "latency": int,
        "carbon_intensity": int,
        "server": {},
    }
    returns: A list with partial task batches
    """
    if algorithm == "latency_greedy":
        mu = 999
    elif algorithm == "carbon_greedy":
        mu = 0
    elif algorithm == "carbon_aware":
        mu = 0.73

    n_tasks = task_batch.load
    # In some way (api/database) get the servers' carbon,latency, capacity
    carbon_intensity = np.array([s.carbon_intensity[t] for s in servers])
    latency = np.array([s.region.latency(task_batch.region) for s in servers])

    capacities = [s.get_utilization_left() for s in servers]
    requests = sched_carb_latency(n_tasks, carbon_intensity, capacities, latency, mu=mu)

    return latency, carbon_intensity, requests


def sched_MILP(req_rates, capacities, latencies, carb_intensities, max_servers, max_latency):
    """
        Schedule the requests and get where the servers should be placed.

        Args:
            param1: req_rates[i] is the number of requests from region i
            param2: capacities[i] is the capacity of servers in region i
            param3: latencies[i][j] is the latency from region i to j
            param4: carb_intensities[i] is the carb intensity in region i
            param5: max_servers is the maximum number of servers
            param6: max_latency is the maximum latency allowed
        Returns:
            x[i][j] is the number of requests from region j that should
            be sent to region i.
            n_servers[i] is the number of servers that should be started
            in region i
    """
    opt_model = plp.LpProblem(name="MILP Model") 
    set_R = range(len(carb_intensities)) # Region set 
    x_vars  = {(i,j): plp.LpVariable(cat=plp.LpInteger, 
                lowBound=0, name=f"x_{i}_{j}") 
                for i in set_R for j in set_R}
    s_vars  = {i: plp.LpVariable(cat=plp.LpInteger, 
                lowBound=0, name=f"s_{i}") 
                for i in set_R}

    {j : opt_model.addConstraint(
        plp.LpConstraint(
            e=plp.lpSum(x_vars[i,j] for i in set_R)-s_vars[j]*capacities[j],
            sense=plp.LpConstraintLE,
            rhs=0,
            name=f"capacity_const{j}")
        )
    for j in set_R}

    opt_model.addConstraint(
        plp.LpConstraint(
            e=plp.lpSum(s_vars[i] for i in set_R),
            sense=plp.LpConstraintLE,
            rhs=max_servers,
            name=f"max_server")
        )

    {j : opt_model.addConstraint(
        plp.LpConstraint(
            e=plp.lpSum(x_vars[i,j] for i in set_R),
            sense=plp.LpConstraintEQ,
            rhs=req_rates[j],#s_vars[j]*capacities[j],
            name=f"sched_all_reqs_const{j}")
        )
    for j in set_R}

    # Latency constraint
    for i,j in zip(set_R, set_R):
        opt_model.addConstraint(
            plp.LpConstraint(
                e=x_vars[i,j]*(latencies[i][j]-max_latency),
                sense=plp.LpConstraintLE,
                rhs=0,#s_vars[j]*capacities[j],
                name=f"latency_const{j}"
            )
        )

    objective = plp.lpSum(x_vars[i,j] * carb_intensities[i] 
                            for i in set_R 
                            for j in set_R)
    opt_model.setObjective(objective) 
    opt_model.solve()
    for v in opt_model.variables():
        if 's' in v.name:
            print(v.name, "=", v.varValue)


def sched_servers():
    pass

def sched_reqs():
    """
        Given a fixed server placement, place the requests among
        them.
    """

sched_MILP([10,10,11]*10, [10,10,10]*10, [[i for i in range(30)] for _ in range(30)]*10, [100, 100, 100]*10, 56, 20)

def sched_carb_latency(n_tasks, carb_intensity, capacities, latency, mu=1):
    """
    Takes a number of fungible tasks from a location, and
    schedules them on servers 1,...,n while considering
    the carbon intensity I_i, latency tau_i and capacity c_i
    of each server i.

    Example: 5 requests to server 1, 10 to
    server 2 and none to server 3 would be [5,10,0]

    Input:
    The number of tasks to be scheduled.

    mu is the unit dependent parameter that
    trade-offs carbon and latency.
    """
    n_servers = len(latency)

    # The objective function's coefficients
    obj_coef = np.concatenate([carb_intensity, mu * latency])

    # Each server can take [0,inf] tasks
    bnd = [(0, float("inf"))] * (2 * n_servers)

    # Capacity constraint. Server i has capacity capacities[i]
    lhs_ineq = np.concatenate([np.identity(n_servers), np.zeros((n_servers, n_servers))], axis=1)
    rhs_ineq = capacities

    # Make sure all tasks are scheduled somewhere.
    lhs_eq = np.zeros((n_servers, 2 * n_servers))
    lhs_eq[0, :n_servers] = 1
    rhs_eq = [n_tasks] + [0] * (n_servers - 1) + [0] * n_servers

    lhs_eq2 = np.concatenate([np.eye(n_servers), -np.eye(n_servers)], axis=1)
    lhs_eq = np.concatenate([lhs_eq, lhs_eq2])

    opt = linprog(
        c=obj_coef, A_ub=lhs_ineq, b_ub=rhs_ineq, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd, method="revised simplex"
    )
    if opt.status == 2:
        print("Warning: No server availible!")
    # print(opt.message)
    # print(f"Objective value: {opt.fun}")
    return np.asarray([math.ceil(x) for x in opt.x][:n_servers])
