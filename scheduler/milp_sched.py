from scipy.optimize import linprog
from scheduler.request import RequestBatch
import numpy as np
import math


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
