import yaml
import argparse
import logging
from .core import make_plot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input yaml file with the workflow specification')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if not args.debug else logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("output.log"),
            logging.StreamHandler()
        ]
    )

    plot_specs = {}
    with open(args.input_file) as f:
        try:
            plot_specs = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)

    for plot in plot_specs['plots']:
        make_plot(plot)



if __name__=="__main__":
    main()