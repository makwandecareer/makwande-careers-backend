from app.services.ai_professional_summary_service import AIProfessionalSummaryService

def test_generate_summary():
    service = AIProfessionalSummaryService()
    result = service.generate(
        profile={"headline": "Software Developer"},
        experience=[{"position":"Developer"}],
        target_role="Backend Developer",
    )

    assert "summary" in result
    assert result["ai_ready"] is True
