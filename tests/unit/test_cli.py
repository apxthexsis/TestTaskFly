from automation_assignment.cli import build_parser


def test_cli_exposes_one_entry_point_with_explicit_subcommands() -> None:
    parser = build_parser()
    readiness = parser.parse_args(["wait-for-api"])
    summary = parser.parse_args(
        [
            "write-summary",
            "--quality-exit",
            "0",
            "--functional-exit",
            "1",
            "--load-exit",
            "0",
        ]
    )

    assert readiness.command == "wait-for-api"
    assert summary.command == "write-summary"
    assert summary.functional_exit == 1
