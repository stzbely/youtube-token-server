import argparse
from database import (
    init_db,
    create_token,
    set_active,
    extend_token,
    list_tokens
)


def main():
    init_db()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create")
    create.add_argument("--user", required=True)
    create.add_argument("--days", type=int, default=30)
    create.add_argument("--devices", type=int, default=1)

    disable = sub.add_parser("disable")
    disable.add_argument("--token", required=True)

    enable = sub.add_parser("enable")
    enable.add_argument("--token", required=True)

    extend = sub.add_parser("extend")
    extend.add_argument("--token", required=True)
    extend.add_argument("--days", type=int, required=True)

    sub.add_parser("list")

    args = parser.parse_args()

    if args.command == "create":
        token, expires = create_token(
            user=args.user,
            days=args.days,
            max_devices=args.devices
        )
        print("TOKEN:", token)
        print("EXPIRES:", expires)

    elif args.command == "disable":
        set_active(args.token, False)
        print("Disabled:", args.token)

    elif args.command == "enable":
        set_active(args.token, True)
        print("Enabled:", args.token)

    elif args.command == "extend":
        new_date = extend_token(args.token, args.days)
        print("New expires:", new_date)

    elif args.command == "list":
        rows = list_tokens()
        for r in rows:
            print(
                f"{r['token']} | user={r['user']} | active={r['active']} | "
                f"expires={r['expires']} | hwid={r['hwid']}"
            )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()