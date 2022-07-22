#from scipy.optimize import linprog
#from scheduler.task import TaskBatch
import numpy as np
import math
import pulp as plp


def schedule(task_batch, t, servers=None):
    """
        If servers specified, we schedule requests on those.
        Otherwise, we place the servers.
    """
    # In some way (api/database) get the servers' carbon,latency, capacity
    carbon_intensities = np.array([s.carbon_intensity[t] for s in servers])
    latencies = np.array([s.region.latency(task_batch.region) for s in servers])

    capacities = [s.get_utilization_left() for s in servers]
    if servers:
        requests = sched_reqs([task.load for task in task_batch], capacities,
                    latencies, carb_intensities, max_servers, max_latency)
    else:
        servers = place_servers(n_tasks, carbon_intensity, capacities, latency, mu=mu)

    return latency, carbon_intensity, requests


def place_servers(req_rates, capacities, latencies, carb_intensities, max_servers, max_latency):
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
            rhs=req_rates[j],
            name=f"sched_all_reqs_const{j}")
        )
    for j in set_R}

    # Latency constraint
    for i,j in zip(set_R, set_R):
        opt_model.addConstraint(
            plp.LpConstraint(
                e=x_vars[i,j]*(latencies[i][j]-max_latency),
                sense=plp.LpConstraintLE,
                rhs=0,
                name=f"latency_const{j}"
            )
        )

    objective = plp.lpSum(x_vars[i,j] * carb_intensities[i] 
                            for i in set_R 
                            for j in set_R)
    opt_model.setObjective(objective) 
    opt_model.solve()
    if opt_model.sol_status != 1:
        print('Did not find sol!')

    return [int(s.varValue) for s in s_vars.values()]

#a = place_servers([10,10,11]*10, [10,10,10]*10, [[i for i in range(30)] for _ in range(30)]*10, [100, 100, 100]*10, 56, 20)
#print(a)

def sched_reqs(req_rates, capacities, latencies, carb_intensities, servers, max_latency):
    """
        Given a fixed server placement, place the requests among
        them.
    """
    opt_model = plp.LpProblem(name="MILP Model") 
    set_R = range(len(carb_intensities)) # Region set 
    x_vars  = {(i,j): plp.LpVariable(cat=plp.LpInteger, 
                lowBound=0, name=f"x_{i}_{j}") 
                for i in set_R for j in set_R}

    {j : opt_model.addConstraint(
        plp.LpConstraint(
            e=plp.lpSum(x_vars[i,j] for i in set_R)-servers[j]*capacities[j],
            sense=plp.LpConstraintLE,
            rhs=0,
            name=f"capacity_const{j}")
        )
    for j in set_R}

    # Sum of request rates lambda must be equal to number of 
    # requests scheduled
    {j : opt_model.addConstraint(
        plp.LpConstraint(
            e=plp.lpSum(x_vars[i,j] for i in set_R),
            sense=plp.LpConstraintEQ,
            rhs=req_rates[j],
            name=f"sched_all_reqs_const{j}")
        )
    for j in set_R}

    # Latency constraint
    for i,j in zip(set_R, set_R):
        opt_model.addConstraint(
            plp.LpConstraint(
                e=x_vars[i,j]*(latencies[i][j]-max_latency),
                sense=plp.LpConstraintLE,
                rhs=0,
                name=f"latency_const{j}"
            )
        )

    objective = plp.lpSum(x_vars[i,j] * carb_intensities[i] 
                            for i in set_R 
                            for j in set_R)
    opt_model.setObjective(objective) 
    opt_model.solve()
    if opt_model.sol_status != 1:
        print('Did not find sol!')
    requests = np.zeros((len(set_R), len(set_R)))
    for i,j in x_vars.keys():
        requests[i,j]= x_vars[i,j].varValue
    return requests
#a = sched_reqs([10,10,11]*10, [10,10,10]*10, [[i for i in range(30)] for _ in range(30)]*10,
             [100, 100, 100]*10, [10,10,10]*10, 20)
#print(a)