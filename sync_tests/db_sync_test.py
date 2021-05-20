import argparse

from sync_tests.utils import get_current_date_time


def main():
    start_test_time = get_current_date_time()
    print(f"Start test time:            {start_test_time}")

    tag_no1 = str(vars(args)["node_tag_no1"]).strip()
    tag_no2 = str(vars(args)["node_tag_no2"]).strip()
    print(f"node_tag_no1: {tag_no1}")
    print(f"node_tag_no2: {tag_no2}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute basic sync test\n\n")

    parser.add_argument(
        "-dt1", "--db_tag_no1", help="db sync tag no1 - used for initial sync, from clean state"
    )
    parser.add_argument(
        "-dt2", "--db_tag_no2", help="db sync tag no2- used for final sync, from existing state"
    )

    args = parser.parse_args()

    main()

