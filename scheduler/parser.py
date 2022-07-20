import argparse


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--algorithm",
        choices=["latency_greedy", "carbon_greedy", "carbon_aware"],
        help="The scheduling algorithm to use",
        default="carbon_aware",
    )

    parser.add_argument(
        "-dt",
        "--timesteps",
        type=int,
        help="The total number of hours",
        default=24,
    )

    parser.add_argument(
        "-ds",
        "--tasks-per-timestep",
        type=int,
        help="The number of times per timestep that task batches are generated",
        default=6,
    )

    parser.add_argument(
        "-l",
        "--file-to-load",
        type=str,
        help="Name of file to load and plot"
    )

    parser.add_argument(
        "-s",
        "--file-to-save",
        type=str,
        help="Name of file to save and plot",
        default="plotting_data"
    )

    return parser.parse_args(argv)
