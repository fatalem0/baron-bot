import argparse

from configs import models
from baron.start import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=models.Environment, required=False, default=models.Environment.local)
    args = parser.parse_args()
    config = models.load_config(args.env)
    main(config)
