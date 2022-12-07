import argparse


def start():
    parse_args()


def init_args():
    """Init all the command line arguments."""
    parser = argparse.ArgumentParser(
        prog="spotdj",
        conflict_handler="resolve",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        dest="debug",
        help="enable debug mode",
    )

    return parser


def parse_args():
    """Parse command line arguments."""
    init_args().parse_args()
