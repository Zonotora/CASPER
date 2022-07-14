import argparse


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--algorithm",
        choices=["latency_greedy", "carbon_greedy", "carbon_aware"],
        help="The scheduling algorithm to use",
        default="latency_greedy",
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
        "--tasks_per-hour",
        type=int,
        help="The number of times per hour that task batches are generated",
        default=6,
    )

    return parser.parse_args(argv)
