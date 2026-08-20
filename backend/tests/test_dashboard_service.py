from unittest.mock import MagicMock

from app.services.dashboard_service import DashboardService


def _query_result(
    *,
    scalar=None,
    all_result=None,
):
    query = MagicMock()

    query.scalar.return_value = scalar
    query.all.return_value = (
        all_result
        if all_result is not None
        else []
    )

    query.filter.return_value = query
    query.group_by.return_value = query

    return query


def test_dashboard_summary():
    db = MagicMock()

    db.query.side_effect = [
        _query_result(
            all_result=[
                ("critical", 2),
                ("high", 3),
                ("medium", 4),
                ("low", 5),
            ]
        ),
        _query_result(scalar=14),

        _query_result(
            all_result=[
                ("critical", 3),
                ("high", 5),
                ("medium", 7),
                ("low", 9),
            ]
        ),
        _query_result(scalar=24),
        _query_result(scalar=10),

        _query_result(
            all_result=[
                ("critical", 1),
                ("high", 2),
                ("medium", 3),
                ("low", 4),
            ]
        ),
        _query_result(scalar=10),
        _query_result(scalar=4),

        _query_result(
            all_result=[
                ("critical", 4),
                ("high", 5),
                ("medium", 6),
                ("low", 7),
            ]
        ),
        _query_result(scalar=22),
        _query_result(scalar=12),
    ]

    service = DashboardService(db=db)

    result = service.get_summary()

    assert result.assets.total == 14
    assert result.assets.critical == 2
    assert result.assets.high == 3
    assert result.assets.medium == 4
    assert result.assets.low == 5

    assert result.alerts.total == 24
    assert result.alerts.open == 10
    assert result.alerts.critical == 3

    assert result.incidents.total == 10
    assert result.incidents.open == 4
    assert result.incidents.critical == 1

    assert result.findings.total == 22
    assert result.findings.open == 12
    assert result.findings.critical == 4


def test_dashboard_handles_empty_database():
    db = MagicMock()

    db.query.side_effect = [
        _query_result(all_result=[]),
        _query_result(scalar=0),

        _query_result(all_result=[]),
        _query_result(scalar=0),
        _query_result(scalar=0),

        _query_result(all_result=[]),
        _query_result(scalar=0),
        _query_result(scalar=0),

        _query_result(all_result=[]),
        _query_result(scalar=0),
        _query_result(scalar=0),
    ]

    service = DashboardService(db=db)

    result = service.get_summary()

    assert result.assets.total == 0
    assert result.alerts.total == 0
    assert result.alerts.open == 0
    assert result.incidents.total == 0
    assert result.incidents.open == 0
    assert result.findings.total == 0
    assert result.findings.open == 0
