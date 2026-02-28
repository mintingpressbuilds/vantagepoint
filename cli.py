import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="VantagePoint")
    sub = parser.add_subparsers(dest="command")
    serve = sub.add_parser("serve", help="Start API server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8001)
    rp = sub.add_parser("run", help="Start interactive session")
    rp.add_argument("friction", type=str, help="What's wrong?")
    args = parser.parse_args()
    if args.command == "serve":
        uvicorn.run("api.server:app", host=args.host, port=args.port)
    elif args.command == "run":
        from main import run_interactive
        session = run_interactive(args.friction)
        print(f"Session started: {session.id}")
        print(f"Mode: {session.mode}")
        print("Use the API to continue: POST /session/{id}/calibrate")


if __name__ == "__main__":
    main()
