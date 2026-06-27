from app.guard import ScopeClassification


def test_scope_classification_acceptance_properties() -> None:
    result = ScopeClassification(label="domestic_tourism")

    assert result.is_tourism_related is True


def test_scope_classification_rejection_properties() -> None:
    result = ScopeClassification(
        label="out_of_scope", reason="llm_classified_out_of_scope"
    )

    assert result.is_tourism_related is False
