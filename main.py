import argparse
import sys
from agent.main_agent import run


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Power BI Engineer — generates .pbix dashboards from CSV + natural language."
    )
    parser.add_argument("command", type=str, help='Natural language command, e.g. "Analyze Q3 sales and build a dashboard"')
    parser.add_argument("csv", type=str, help="Path to the input CSV file")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory (default: output/<timestamp>)")

    args = parser.parse_args()

    print(f"Running agent...\nCommand: {args.command}\nCSV: {args.csv}\n")

    try:
        result = run(args.command, args.csv, output_dir=args.output_dir)
        print(f"\nDone!")
        print(f"  Dashboard: {result['pbix_path']}")
        print(f"  Report:    {result['report_path']}")
        if result.get("reviewer_feedback"):
            print(f"  Reviewer:  {result['reviewer_feedback']}")
    except RuntimeError as e:
        print(f"\nAgent stopped: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
