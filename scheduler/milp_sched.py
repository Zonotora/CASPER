import numpy as np
import pulp as plp
import logging



def schedule_servers(conf, request_batches, server_manager, t, max_servers=4, max_latency=100):
    """
    Wrapper around the CAP (place_servers()).

    Setting max_latency to infinity makes algorithm carbon greedy.

    Args:
        conf:
        request_batches: request_batches[i] is the requests from region i
        server_manager: server manager object
        t: time-step
        max_servers: Maximum number of servers. Defaults to 4.
        max_latency: Maximum latency tolerated. Defaults to 100.

    Returns:
        server[i] - number of servers in region i.
    """

    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    # TODO: We should not allow nans
    latencies[np.isnan(latencies)] = 1

    capacities = [conf.server_capacity] * len(server_manager.regions)
    request_rates = [batch.load for batch in request_batches]
    # reqs are the tentative requests
    scheduler = conf.type_scheduler
    servers, reqs, obj_val = place_servers(
        scheduler, request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency
    )
    if obj_val < 0:
        logging.warning(
            f"Could not place servers! t={t} reqs: {request_rates} caps: {capacities} max_servers: {max_servers}"
        )
        raise Exception("Could not place, look above for more info")
    # print(f"At t={t} servers placed: {servers} obj_val:{obj_val}")
    # If we never plan to schedule at a region, we set the servers in that region to 0.
    mask = np.sum(reqs, axis=0) == 0
    servers[mask] = 0

    return servers

def place_servers(scheduler, request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency):
    """Organizes choice of scheduler
    """
    assert str(scheduler) in ["latency", "carbon"], scheduler
    if scheduler == "carbon":
        return place_servers_carbon_greedy(request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency)
    elif scheduler == "latency":
        return place_servers_latency_greedy(request_rates, capacities, latencies, carbon_intensities, max_servers)

def schedule_requests(conf, request_batches, server_manager, t, request_update_interval, max_latency=100):
    """
    Wrapper around the CAS (sched_reqs()).

    Setting max_latency to infinity makes algorithm carbon greedy.

    Args:
        conf:
        request_batches: request_batches[i] is the requests from region i
        server_manager: server manager object
        t: time-step
        request_update_interval: Interval in minutes in which requests are scheduled.
        max_latency: Maximum latency tolerated. Defaults to 100.

    Returns:
        requests[i,j] - number of requests from region i to j.
    """

    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    # TODO: We should not allow nans
    latencies[np.isnan(latencies)] = 1

    capacities = [conf.server_capacity // request_update_interval] * len(server_manager.regions)
    request_rates = [batch.load for batch in request_batches]
    servers = server_manager.servers_per_region()

    obj_val = 0
    if conf.type_scheduler == "carbon":
        requests, obj_val = sched_reqs_carbon_greedy(request_rates, capacities, latencies, carbon_intensities, servers, max_latency)
        check_obj_valid(obj_val)
        return latencies, carbon_intensities, requests

    elif conf.type_scheduler == "latency":
        requests, obj_val = sched_reqs_latency_greedy(request_rates, capacities, latencies, carbon_intensities, servers)
        check_obj_valid(obj_val)
        return latencies, carbon_intensities, requests

    elif conf.type_scheduler == "replay":
        # requests = load_request_matrix()
        # return latencies, carbon_intensities, requests
        pass

    # print(f"At t={t}, obj_val={obj_val:e} g C02 requests scheduled at: \n{requests}")

def check_obj_valid(obj_val):
    if obj_val < 0:
        logging.warning(
            f"Could not schedule requests! t={t} reqs: {request_rates} caps: {capacities} servers: {servers}"
        )
        raise Exception("Could not schedule, look above for more info")

def place_servers_latency_greedy(request_rates, capacities, latencies, carbon_intensities, max_servers):
    """
    This is the latency greedy scheduler to compare with the Carbon Aware Scheduler. The placement
    of servers are determined by latency rather than by carbon.

    If problem was not solved, a negative objective value is returned

    Args:
        request_rates: request_rates[i] is the number of requests from region i
        capacities: capacities[i] is the average capacity per server in region i
        latencies: latencies[i][j] is the latency from region i to j
        carbon_intensities: carbon_intensities[i] is the carbon intensity in region i
        max_servers: max_servers is the maximum number of servers
        max_latency: max_latency is the maximum latency allowed
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

    objective = plp.lpSum(latencies[i][j] * x_vars[i, j] for i in set_R for j in set_R)

    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    requests = np.zeros((len(set_R), len(set_R)), dtype=int)
    for i, j in x_vars.keys():
        requests[i, j] = int(x_vars[i, j].varValue)

    if opt_model.sol_status != 1:
        return np.zeros(n_regions), requests, -10000

    return np.array([int(s.varValue) for s in s_vars.values()]), requests, objective.value()


def place_servers_carbon_greedy(request_rates, capacities, latencies, carbon_intensities, max_servers, max_latency):
    """
    This is the Carbon Aware Provisioner (CAP) where the placement of servers are determined.
    For example if one region have a low carbon intensity for the next hours, more servers
    should be allocated there.

    If problem was not solved, a negative objective value is returned

    Args:
        request_rates: request_rates[i] is the number of requests from region i
        capacities: capacities[i] is the average capacity per server in region i
        latencies: latencies[i][j] is the latency from region i to j
        carbon_intensities: carbon_intensities[i] is the carbon intensity in region i
        max_servers: max_servers is the maximum number of servers
        max_latency: max_latency is the maximum latency allowed
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
                    name=f"latency_const{i}_{j}",
                )
            )

    objective = plp.lpSum(x_vars[i, j] * carbon_intensities[j] for i in set_R for j in set_R)

    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    requests = np.zeros((len(set_R), len(set_R)), dtype=int)
    for i, j in x_vars.keys():
        requests[i, j] = int(x_vars[i, j].varValue)

    if opt_model.sol_status != 1:
        return np.zeros(n_regions), requests, -10000

    return np.array([int(s.varValue) for s in s_vars.values()]), requests, objective.value()


def sched_reqs_carbon_greedy(request_rates, capacities, latencies, carbon_intensities, servers, max_latency):
    """
    This is the Carbon Aware Scheduler (CAS).
    CAS schedules the requests given a fixed server placement that has been determined by
    the CAP.
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
                    name=f"latency_const{i}_{j}",
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

def sched_reqs_latency_greedy(request_rates, capacities, latencies, carbon_intensities, servers):
    """
    This is the Carbon Aware Scheduler (CAS).
    CAS schedules the requests given a fixed server placement that has been determined by
    the CAP.
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

    objective = plp.lpSum(x_vars[i, j] * latencies[i][j] for i in set_R for j in set_R)
    opt_model.setObjective(objective)
    opt_model.solve(plp.PULP_CBC_CMD(msg=0))
    requests = np.zeros((len(set_R), len(set_R)), dtype=int)
    for i, j in x_vars.keys():
        requests[i, j] = int(x_vars[i, j].varValue)

    if opt_model.sol_status != 1:
        #        print("[x] Did not find a request schedule! Returning all 0's")
        return np.zeros((n_regions, n_regions)), -10000
    return requests, objective.value()
