import numpy as np
import pulp as plp
import logging


def schedule_servers(conf, request_batches, server_manager, t, max_servers=4, max_latency=100):
    """
    Place servers

    Setting max_latency to infinity makes algorithm carbon greedy.
    Setting max_latency to 0 makes it always choose all servers in
    the same region
    """
    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    capacities = [conf.server_capacity] * len(server_manager.regions)
    request_rates = [batch.load for batch in request_batches]

    # reqs are the tentative requests
    servers, reqs, obj_val = place_servers(
        request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency
    )
    if obj_val < 0:
        logging.warning(
            f"Could not place servers! t={t} reqs: {request_rates} caps: {capacities} max_servers: {max_servers}"
        )
    # print(f"At t={t} servers placed: {servers} obj_val:{obj_val}")
    return servers


def schedule_requests(conf, request_batches, server_manager, t, request_update_interval, max_latency=100):
    """
    Schedule requests

    Setting max_latency to infinity makes algorithm carbon greedy.
    Setting max_latency to 0 makes it always choose all servers in
    the same region
    """
    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    capacities = [conf.server_capacity // request_update_interval] * len(server_manager.regions)
    request_rates = [batch.load for batch in request_batches]
    servers = server_manager.servers_per_region()
    requests, obj_val = sched_reqs(request_rates, capacities, latencies, carbon_intensities, servers, max_latency)
    if obj_val < 0:
        logging.warning(
            f"Could not schedule requests! t={t} reqs: {request_rates} caps: {capacities} servers: {servers}"
        )
    # print(f"At t={t}, obj_val={obj_val:e} g C02 requests scheduled at: \n{requests}")
    return latencies, carbon_intensities, requests


def place_servers(request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency):
    """
    Schedule the requests and get where the servers should be placed.
    If problem was not solved, a negative objective value is returned

    Args:
        param1: req_rates[i] is the number of requests from region i
        param2: capacities[i] is the aggregate capacity of servers in region i
        param3: latencies[i][j] is the latency from region i to j
        param4: carb_intensities[i] is the carb intensity in region i
        param5: max_servers is the maximum number of servers
        param6: max_latency is the maximum latency allowed
    Returns:
        return1: x[i][j] is the number of requests from region i that should
        be sent to region j.
        return2: n_servers[i] is the number of servers that should be started
        in region i.
        return3: objective value. 
    """

    opt_model = plp.LpProblem(name="model")
    n_regions = len(carbon_intensities)
    set_R = range(n_regions)  # Region set
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
    for i in set_R:
        for j in set_R:
            opt_model.addConstraint(
                plp.LpConstraint(
                    e=x_vars[i, j] * (latencies[i][j] - max_latency),
                    sense=plp.LpConstraintLE,
                    rhs=0,
                    name=f"latency_const{i}{j}",
                )
            )

    objective = plp.lpSum(x_vars[i, j] * carbon_intensities[j] for i in set_R for j in set_R)
    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    requests = np.zeros((len(set_R), len(set_R)), dtype=int)
    for i, j in x_vars.keys():
        requests[i, j] = int(x_vars[i, j].varValue)

    if opt_model.sol_status != 1:
        #        print("[x] Did not find a server placement! Returning all 0's")
        return [0] * n_regions, requests, -10000

    return [int(s.varValue) for s in s_vars.values()], requests, objective.value()


def sched_reqs(request_rates, capacities, latencies, carbon_intensities, servers, max_latency):
    """
    Given a fixed server placement, place the requests among
    them. req_rates are the rate FROM each region.
    """

    opt_model = plp.LpProblem(name="model")
    n_regions = len(carbon_intensities)
    set_R = range(n_regions)  # Region set
    x_vars = {(i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R}

    for j in set_R:
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(x_vars[i, j] for i in set_R) - servers[j] * capacities[j],
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
    for i in set_R:
        for j in set_R:
            opt_model.addConstraint(
                plp.LpConstraint(
                    e=x_vars[i, j] * (latencies[i][j] - max_latency),
                    sense=plp.LpConstraintLE,
                    rhs=0,
                    name=f"latency_const{i}{j}",
                )
            )

    objective = plp.lpSum(x_vars[i, j] * carbon_intensities[j] for i in set_R for j in set_R)
    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    requests = np.zeros((len(set_R), len(set_R)), dtype=int)
    for i, j in x_vars.keys():
        requests[i, j] = int(x_vars[i, j].varValue)

    if opt_model.sol_status != 1:
        #        print("[x] Did not find a request schedule! Returning all 0's")
        return np.zeros((n_regions, n_regions)), -10000
    return requests, objective.value()
