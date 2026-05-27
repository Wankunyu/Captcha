import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an explicit provider smoke test using local configuration."
    )
    parser.add_argument(
        "--provider",
        required=True,
        help="Provider name, e.g. openai or openrouter",
    )
    parser.add_argument("--model", required=True, help="Provider model label")
    parser.add_argument("--secrets-file", default="./secrets.yaml", help="Local config path")
    parser.add_argument("--timeout-sec", type=float, default=120.0, help="Provider timeout seconds")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming when supported")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    from cognition.revision_secrets import load_local_config
    from cognition.run_eval import build_json_schema, make_provider

    print(f"[INFO] provider={args.provider} model={args.model}")
    secrets = load_local_config(args.secrets_file)
    provider = make_provider(
        args.provider,
        args.model,
        secrets,
        timeout_sec=args.timeout_sec,
    )
    schema = build_json_schema("Dice_Count")
    raw, parsed, _meta = provider.infer(
        prompt="Return a JSON answer for a provider smoke check.",
        images=[],
        json_schema=schema,
        stream=not args.no_stream,
    )
    if parsed is None and not raw:
        raise RuntimeError("provider smoke returned no response")
    print("[DONE] provider smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
