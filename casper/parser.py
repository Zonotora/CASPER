import argparse


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t",
        "--timesteps",
        type=int,
        help="The total number of hours",
        default=24,
    )

    parser.add_argument(
        "-u",
        "--request-update-interval",
        type=int,
        help="The number of minutes between each scheduling",
        choices=range(0, 61),
        metavar="[0-60]",
        default=10,
    )

    parser.add_argument(
        "-r",
        "--request-rate",
        type=int,
        help="Specify a constant request rate per hour",
    )

    parser.add_argument(
        "--save",
        help="Save file to /saved with the following format YYYY-MM-DD_hh:mm:ss",
        action="store_true",
    )

    parser.add_argument(
        "-d",
        "--start-date",
        type=str,
        help="Start date in ISO format (YYYY-MM-DD)",
        default="2022-08-03",
    )

    parser.add_argument(
        "--max-latency",
        type=int,
        help="Maximum latency allowed",
        default=100000,
    )

    parser.add_argument(
        "--max-servers",
        type=int,
        help="Maximum pool of servers",
        default=1000,
    )

    parser.add_argument(
        "--server-capacity",
        type=int,
        help="The capacity of each server",
        default=1_000_000,
    )

    parser.add_argument(
        "--region",
        type=str,
        choices=["na", "eu"],
        help="The region we want to load our data from",
        default="na",
    )

    parser.add_argument(
        "--scheduler",
        type=str,
        choices=["carbon", "latency"],
        help="Define what you wish to minimize: carbon/latency",
        default="carbon",
    )

    parser.add_argument(
        "--replay",
        action="store_true",
        help="Use akamai dataset instead of MILP scheduler to produce output",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print information for every timestep",
    )

    parser.add_argument(
        "--verbose-milp",
        action="store_true",
        help="Print the log from the MILP scheduler",
    )

    return parser.parse_args(argv)
