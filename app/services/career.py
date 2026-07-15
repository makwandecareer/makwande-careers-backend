from app.schemas import CareerGuidanceRequest, CareerGuidanceResponse

def generate_career_guidance(
    request: CareerGuidanceRequest,
) -> CareerGuidanceResponse:
    strengths = request.skills[:5]

    if not strengths:
        strengths = [
            "Your existing education and experience should be reviewed against the target role."
        ]

    gaps = [
        f"Compare your current profile with at least three recent {request.target_role} job descriptions."
    ]

    next_steps = [
        "Identify the most common required skills.",
        "Collect evidence of projects, achievements and work experience.",
        "Update your CV using accurate and verified information only.",
        "Build one practical project for your highest-priority skills gap.",
        "Request professional feedback before applying.",
    ]

    return CareerGuidanceResponse(
        strengths=strengths,
        gaps=gaps,
        next_steps=next_steps,
    )
