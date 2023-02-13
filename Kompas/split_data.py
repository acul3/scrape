import argparse
from pathlib import Path
import sys
import random
import shutil


def main():
    """
    This function split the json files in to train and test set.
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="Input directory")
    parser.add_argument("-o", "--output_dir", type=str, required=False,
                        help="Output directory")
    parser.add_argument("-t", "--train_split", type=float, required=False, default=0.5,
                        help="The percentage of train set (from 0.0 to 1.0)")
    parser.add_argument("-s", "--seed", type=int, required=False, default=0,
                        help="The random seed number")
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    train_split = args.train_split
    random.seed(args.seed)

    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist")
        sys.exit(1)
    train_dir = output_dir / "train"
    test_dir = output_dir / "test"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    for file in input_dir.glob("**/*.json"):
        if random.random() < train_split:
            destination_file = train_dir/file.relative_to(input_dir)
            destination_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            destination_file = test_dir/file.relative_to(input_dir)
            destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, destination_file)


if __name__ == '__main__':
    main()
