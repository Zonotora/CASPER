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
        "-t",
        "--timesteps",
        type=int,
        help="The total number of hours",
        default=24,
    )

    parser.add_argument(
        "-r",
        "--request-update-interval",
        type=int,
        help="The number of minutes between each scheduling",
        choices=range(0, 61),
        metavar="[0-60]",
        default=10,
    )

    parser.add_argument("-l", "--file-to-load", type=str, help="Name of file to load and plot")

    parser.add_argument("-s", "--file-to-save", type=str, help="Name of file to save and plot")

    # TODO: Use this or remove it
    parser.add_argument(
        "-d",
        "--requests-date",
        type=str,
        help="Date of requests in format Y-M-D. Takes for all hours that day",
        default="plotting_data",
    )

    return parser.parse_args(argv)
