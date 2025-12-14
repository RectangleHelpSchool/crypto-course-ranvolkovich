import asyncio
import sys
from approvalfetcher.utils.cli import parse_args
from approvalfetcher.app import ApprovalFetcherApp


def main() -> None:

    args = parse_args()
    app = ApprovalFetcherApp(
        infura_api_key=args.infura_key,
        log_level=args.log_level
    )

    try:
        result = asyncio.run(app.run(args.address))
        print(result)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()