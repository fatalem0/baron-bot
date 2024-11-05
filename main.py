import argparse

from baron.commands import main
from configs import models

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=models.Environment, required=False, default=models.Environment.local)
    args = parser.parse_args()
    config = models.load_config(args.env)
    main(config)
