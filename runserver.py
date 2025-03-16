"""
Processes cli and runs the flask server if conditions satisfy
"""
import sys
import os
import argparse
from app import app


def cli_parser():
    """
    Parses command line and displays help messsage with -h
    """
    parser = argparse.ArgumentParser(
        prog= "runserver.py",
        description= "The YUAG search application",
        allow_abbrev=False,
    )
    parser.add_argument('port', type=int, help='the port at which the server should listen')

    return parser.parse_args()

def main():
    """
    Main function calls all the other functions to make it work
    """
    #parse cli and get the port from it
    args = cli_parser()

    # Check for valid port
    try:
        port_num = int(args.port)
        if port_num <= 0:
            print("Error: port must be a positive integer.", file=sys.stderr)
            sys.exit(1)
    except ValueError:
        print("Error: port must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    # Check if database exists
    if not os.path.exists("lux.sqlite"):
        print("Error: Database file 'lux.sqlite' does not exist.", file=sys.stderr)
        sys.exit(1)
    app.run(host='0.0.0.0', port=args.port)

if __name__ == "__main__":
    main()
