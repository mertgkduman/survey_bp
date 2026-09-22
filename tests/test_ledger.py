"""Shot accounting must survive failures and replay."""


def test_empty_journal_has_no_final_rows(tmp_path):
    from bp_registry.ledger import reconcile

    path = tmp_path / "events.jsonl"
    path.write_text("")
    assert reconcile(path) == []


def test_unmatched_begin_is_interrupted(tmp_path):
    from bp_registry.ledger import Writer, reconcile

    path = tmp_path / "events.jsonl"
    writer = Writer(path)
    writer.begin(run_id="r1", shot_id=1)
    writer.close()
    rows = reconcile(path)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "r1"
    assert rows[0]["shot_id"] == 1
    assert rows[0]["termination"] == "interrupted"


def test_duplicate_begin_does_not_create_second_final_row(tmp_path):
    from bp_registry.ledger import Writer, reconcile

    path = tmp_path / "events.jsonl"
    writer = Writer(path)
    writer.begin(run_id="r1", shot_id=1)
    try:
        writer.begin(run_id="r1", shot_id=1)
    except ValueError:
        pass
    writer.close()
    assert len(reconcile(path)) == 1

