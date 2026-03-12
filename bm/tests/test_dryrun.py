from bm.dryrun import DryRunContext, DryRunOp


def test_record_noop_when_not_dry_run() -> None:
    ctx = DryRunContext(dry_run=False)
    ctx.record("symlink", "~/.claude/skills/foo", "skills/foo")
    assert ctx.ops == []


def test_record_collects_ops_when_dry_run() -> None:
    ctx = DryRunContext(dry_run=True)
    ctx.record("symlink", "~/.claude/skills/foo", "skills/foo")
    ctx.record("registry_add", "foo")
    assert len(ctx.ops) == 2
    assert ctx.ops[0] == DryRunOp(
        verb="symlink", target="~/.claude/skills/foo", source="skills/foo"
    )
    assert ctx.ops[1] == DryRunOp(verb="registry_add", target="foo", source="")


def test_has_changes_false_when_no_ops() -> None:
    ctx = DryRunContext(dry_run=True)
    assert not ctx.has_changes


def test_has_changes_true_when_ops_recorded() -> None:
    ctx = DryRunContext(dry_run=True)
    ctx.record("remove", "~/.claude/skills/bar")
    assert ctx.has_changes


def test_noop_context_convenience() -> None:
    ctx = DryRunContext()  # dry_run defaults to False
    ctx.record("remove", "anything")
    assert ctx.ops == []
