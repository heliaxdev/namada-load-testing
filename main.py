import argparse
import logging
import os

from src.config import Config
from src.coordinator import Coordinator

log_level = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=log_level)


def run(args: argparse.Namespace):
    config = Config.read(args.config_path)

    Coordinator.run(config, args.seeds, args.nodes, args.base_directory, args.base_binary, args.fail_fast, args.json_output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Namada Load tester utility.')
    parser.add_argument("-bd", "--base-directory", type=str, action='store', required=True,
                        help='Path to binaries directory.')
    parser.add_argument("-s", "--seeds", nargs='*', action='store', help='Space separated list of seeds.', required=True)
    parser.add_argument("-n", "--nodes", nargs='*', action='store', help='Space separated list of nodes (ip:port).', required=True)
    parser.add_argument("-bb", "--base-binary", type=str, action='store', help='Base binary.', default='namada')
    parser.add_argument("-c", "--config-path", type=str, action='store', help='Path to config file.',
                        default="configs/conf.yaml")
    parser.add_argument("-ff", "--fail-fast", action='store_true', help='Fail if any tx fail.', default=False)
    parser.add_argument("-jo", "--json-output", action='store_true', help='Dump result as json', default=False)

    args = parser.parse_args()

    run(args)
