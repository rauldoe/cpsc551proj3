import yaml
import argparse

def read_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', metavar='file', type=str, default='tuplespace.yaml')

    args = parser.parse_args()

    return read_config_filename(args.config)

def read_config_filename(filename):

    with open(filename, 'r') as stream:
        return yaml.safe_load(stream)
