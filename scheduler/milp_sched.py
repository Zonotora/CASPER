import numpy as np
import math
import pulp as plp


def schedule_servers(request_batches, server_manager, t, max_servers=10, max_latency=100):
    """
    Place servers
    """
    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    capacities = server_manager.utilization_left_regions()
    request_rates = [batch.load for batch in request_batches]
    # servers_per_region = server_manager.servers_per_region()
    servers = place_servers(request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency)
    return servers


def schedule_requests(request_batches, server_manager, t, max_latency=100):
    """
    Schedule requests
    """
    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    capacities = server_manager.utilization_left_regions()
    request_rates = [batch.load for batch in request_batches]
    #    servers_per_region = server_manager.servers_per_region()
    requests = sched_reqs(request_rates, capacities, latencies, carbon_intensities, max_latency)
    return latencies, carbon_intensities, requests


def place_servers(request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency):
    """
    Schedule the requests and get where the servers should be placed.

    Args:
        param1: req_rates[i] is the number of requests from region i
        param2: capacities[i] is the aggregate capacity of servers in region i
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
    set_R = range(len(carbon_intensities))  # Region set
    x_vars = {(i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R}
    s_vars = {i: plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"s_{i}") for i in set_R}

    # Cap the number of servers
    opt_model.addConstraint(
        plp.LpConstraint(
            e=plp.lpSum(s_vars[i] for i in set_R), sense=plp.LpConstraintLE, rhs=max_servers, name="max_server"
        )
    )

    # Per server max capacity
    for j in set_R:
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(x_vars[i, j] for i in set_R) - s_vars[j] * capacities[j],
                sense=plp.LpConstraintLE,
                rhs=0,
                name=f"capacity_const{j}",
            )
        )

    # All requests from a region must go somewhere.
    for i in set_R:
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(x_vars[i, j] for j in set_R),
                sense=plp.LpConstraintEQ,
                rhs=request_rates[i],
                name=f"sched_all_reqs_const{i}",
            )
        )

    # Latency constraint
    for i, j in zip(set_R, set_R):
        opt_model.addConstraint(
            plp.LpConstraint(
                e=x_vars[i, j] * (latencies[i][j] - max_latency),
                sense=plp.LpConstraintLE,
                rhs=0,
                name=f"latency_const{j}",
            )
        )

    objective = plp.lpSum(x_vars[i, j] * carbon_intensities[j] for i in set_R for j in set_R)
    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    if opt_model.sol_status != 1:
        print("Did not find solution!")

    return [int(s.varValue) for s in s_vars.values()]


def sched_reqs(request_rates, capacities, latencies, carbon_intensities, max_latency):
    """
    Given a fixed server placement, place the requests among
    them. req_rates are the rate FROM each region.
    """

    opt_model = plp.LpProblem(name="MILP Model")
    set_R = range(len(carbon_intensities))  # Region set
    x_vars = {(i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R}
    s_vars = {i: plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"s_{i}") for i in set_R}

    for j in set_R:
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(x_vars[i, j] for i in set_R) - capacities[j],
                sense=plp.LpConstraintLE,
                rhs=0,
                name=f"capacity_const{j}",
            )
        )

    # Sum of request rates lambda must be equal to number of
    # requests scheduled
    for i in set_R:
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(x_vars[i, j] for j in set_R),
                sense=plp.LpConstraintEQ,
                rhs=request_rates[i],
                name=f"sched_all_reqs_const{i}",
            )
        )

    # Latency constraint
    for i, j in zip(set_R, set_R):
        opt_model.addConstraint(
            plp.LpConstraint(
                e=x_vars[i, j] * (latencies[i][j] - max_latency),
                sense=plp.LpConstraintLE,
                rhs=0,
                name=f"latency_const{j}",
            )
        )

    objective = plp.lpSum(x_vars[i, j] * carbon_intensities[j] for i in set_R for j in set_R)
    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    if opt_model.sol_status != 1:
        print("Did not find solution!")
    requests = np.zeros((len(set_R), len(set_R)), dtype=int)
    for i, j in x_vars.keys():
        requests[i, j] = int(x_vars[i, j].varValue)
    return requests
