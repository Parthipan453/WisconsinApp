from Research.models import ResearchTeamMember


def research_team_member_status(request):
    is_research_team_member = False

    if request.user.is_authenticated:
        try:
            faculty = request.user.faculty_profile

            is_research_team_member = ResearchTeamMember.objects.filter(
                faculty=faculty,
                role__in=["ADVISOR", "CO_MENTOR"],
            ).exists()

        except Exception:
            is_research_team_member = False

    return {
        "is_research_team_member": is_research_team_member,
    }