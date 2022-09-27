import argparse


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        "--region-kind",
        type=str,
        choices=["na", "eu"],
        help="The region we want to load our data from",
        default="na",
    )

    parser.add_argument(
        "-t", "--timesteps", type=int, help="The total number of hours", default=24,
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

    parser.add_argument(
        "--load", type=str, help="Name of file to load and plot",
    )

    parser.add_argument(
        "--save", help="Save file to /saved with the following format YYYY-MM-DD_hh:mm:ss", action="store_true",
    )

    parser.add_argument(
        "-d", "--start-date", type=str, help="Start date in ISO format (YYYY-MM-DD)", default="2022-08-04",
    )

    parser.add_argument(
        "-v", "--verbose", help="Print information for every timestep", action="store_true",
    )

    parser.add_argument(
        "-l", "--latency", type=int, help="Maximum latency allowed", default=100000,
    )

    parser.add_argument(
        "-m", "--max-servers", type=int, help="Maximum pool of servers", default=1000,
    )

    parser.add_argument(
        "--rate", type=int, help="Specify a constant request rate per hour",
    )

    parser.add_argument(
        "-c", "--server-capacity", type=int, help="The capacity of each server", default=1000_000_000,
    )

    parser.add_argument(
        "-ty", "--type-scheduler", type=str, help="Define what you wish to minimize: carbon/latency", default="carbon"
    )

    parser.add_argument(
        "--verbose-milp",
        action="store_true",
        help="Print the log from the MILP scheduler",
    )


    return parser.parse_args(argv)

