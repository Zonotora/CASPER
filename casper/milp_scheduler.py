import numpy as np
import pulp as plp
import logging


class Latency:
    @staticmethod
    def schedule_servers(
        conf,
        carbon_intensities,
        latencies,
        capacities,
        request_rates,
        max_servers,
        max_latency,
    ):
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
        x_vars = {
            (i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R
        }
        s_vars = {i: plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"s_{i}") for i in set_R}

        # Cap the number of servers
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(s_vars[i] for i in set_R),
                sense=plp.LpConstraintLE,
                rhs=max_servers,
                name="max_server",
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
        opt_model.solve(plp.PULP_CBC_CMD(msg=conf.verbose_milp))
        requests = np.zeros((len(set_R), len(set_R)), dtype=int)
        for i, j in x_vars.keys():
            requests[i, j] = int(x_vars[i, j].varValue)

        if opt_model.sol_status != 1:
            return np.zeros(n_regions), requests, -10000

        return (
            np.array([int(s.varValue) for s in s_vars.values()]),
            requests,
            objective.value(),
        )

    @staticmethod
    def schedule_requests(
        conf,
        carbon_intensities,
        latencies,
        capacities,
        request_rates,
        servers,
        max_latency,
    ):
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
        x_vars = {
            (i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R
        }

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
        opt_model.solve(plp.PULP_CBC_CMD(msg=conf.verbose_milp))
        requests = np.zeros((len(set_R), len(set_R)), dtype=int)
        for i, j in x_vars.keys():
            requests[i, j] = int(x_vars[i, j].varValue)

        if opt_model.sol_status != 1:
            #        print("[x] Did not find a request schedule! Returning all 0's")
            return np.zeros((n_regions, n_regions)), -10000
        return requests, objective.value()


class Carbon:
    @staticmethod
    def schedule_servers(
        conf,
        carbon_intensities,
        latencies,
        capacities,
        request_rates,
        max_servers,
        max_latency,
    ):
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
        x_vars = {
            (i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R
        }
        s_vars = {i: plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"s_{i}") for i in set_R}

        # Cap the number of servers
        opt_model.addConstraint(
            plp.LpConstraint(
                e=plp.lpSum(s_vars[i] for i in set_R),
                sense=plp.LpConstraintLE,
                rhs=max_servers,
                name="max_server",
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
        opt_model.solve(plp.PULP_CBC_CMD(msg=conf.verbose_milp))
        requests = np.zeros((len(set_R), len(set_R)), dtype=int)
        for i, j in x_vars.keys():
            requests[i, j] = int(x_vars[i, j].varValue)

        if opt_model.sol_status != 1:
            return np.zeros(n_regions), requests, -10000

        return (
            np.array([int(s.varValue) for s in s_vars.values()]),
            requests,
            objective.value(),
        )

    @staticmethod
    def schedule_requests(
        conf,
        carbon_intensities,
        latencies,
        capacities,
        request_rates,
        servers,
        max_latency,
    ):
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
        x_vars = {
            (i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=0, name=f"x_{i}_{j}") for i in set_R for j in set_R
        }

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
        opt_model.solve(plp.PULP_CBC_CMD(msg=conf.verbose_milp))
        requests = np.zeros((len(set_R), len(set_R)), dtype=int)
        for i, j in x_vars.keys():
            requests[i, j] = int(x_vars[i, j].varValue)

        if opt_model.sol_status != 1:
            #        print("[x] Did not find a request schedule! Returning all 0's")
            return np.zeros((n_regions, n_regions)), -10000
        return requests, objective.value()


def compute_args(conf, request_batches, server_manager, t):
    carbon_intensities = [region.carbon_intensity[t] for region in server_manager.regions]
    latencies = np.array(
        [[region.latency(batch.region) for region in server_manager.regions] for batch in request_batches]
    )
    if np.isnan(latencies).any():
        latencies[np.isnan(latencies)] = 10**6
        logging.warning(f"Detected NaN value in latency adjacency matrix. Converted to 10^6 as penalty.")


    capacities = [conf.server_capacity] * len(server_manager.regions)
    # reqs are the tentative requests
    request_rates = np.array([batch.load for batch in request_batches], dtype=np.int64)

    return carbon_intensities, latencies, capacities, request_rates


def validate_objective_value(obj_val, t, carbon_intensities, latencies, capacities, request_rates):
    if obj_val < 0:
        logging.warning(
            f"\nCould not place servers! t={t}\n"
            f"reqs: {request_rates}\n"
            f"caps: {capacities}\n"
            f"acc_reqs={sum(request_rates)}\n"
            f"acc_cap={sum(capacities)}\n"
            f"latency={latencies}\n"
            f"carbon_intenisties={carbon_intensities}\n"
        )
        raise Exception("Infeasible problem, look above for more info")


def schedule_servers(
    conf,
    request_batches,
    server_manager,
    t,
    max_servers,
    max_latency,
):
    """
    Wrapper around the CAP
    """
    args = compute_args(conf, request_batches, server_manager, t)
    place_args = conf, *args, max_servers, max_latency
    if conf.scheduler == "carbon":
        servers, reqs, obj_val = Carbon.schedule_servers(*place_args)
    elif conf.scheduler == "latency":
        servers, reqs, obj_val = Latency.schedule_servers(*place_args)
    else:
        raise Exception("Invalid scheduler")

    validate_objective_value(obj_val, t, *args)

    # If we never plan to schedule at a region, we set the servers in that region to 0.
    mask = np.sum(reqs, axis=0) == 0
    servers[mask] = 0

    return servers


def schedule_requests(
    conf,
    request_batches,
    server_manager,
    t,
    request_update_interval,
    max_latency,
):
    """
    Wrapper around the CAS
    """
    args = compute_args(conf, request_batches, server_manager, t)
    servers = server_manager.servers_per_region()
    schedule_args = conf, *args, servers, max_latency

    if conf.scheduler == "carbon":
        requests, obj_val = Carbon.schedule_requests(*schedule_args)
    elif conf.type_scheduler == "latency":
        requests, obj_val = Latency.schedule_requests(*schedule_args)
    else:
        raise Exception("Invalid scheduler")
    validate_objective_value(obj_val, t, *args)

    carbon_intensities, latencies, *_ = args
    return latencies, carbon_intensities, requests
