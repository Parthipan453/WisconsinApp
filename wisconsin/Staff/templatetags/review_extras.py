from django import template
from django.db.models import QuerySet

register = template.Library()


@register.filter
def get_review(reviews, section_code):
    """Return the SectionReview for *section_code* from a queryset or list."""
    if isinstance(reviews, QuerySet):
        return reviews.filter(section_code=section_code).first()
    for r in reviews:
        if getattr(r, "section_code", None) == section_code:
            return r
    return None


@register.filter
def review_status(reviews, section_code):
    """Return the status string for a section, defaulting to 'not_reviewed'."""
    r = reviews.filter(section_code=section_code).first() if isinstance(reviews, QuerySet) else next(
        (x for x in reviews if getattr(x, "section_code", None) == section_code), None
    )
    return r.status if r else "not_reviewed"


@register.filter
def review_note(reviews, section_code):
    r = reviews.filter(section_code=section_code).first() if isinstance(reviews, QuerySet) else next(
        (x for x in reviews if getattr(x, "section_code", None) == section_code), None
    )
    return r.note if r else ""


@register.filter
def review_internal_note(reviews, section_code):
    r = reviews.filter(section_code=section_code).first() if isinstance(reviews, QuerySet) else next(
        (x for x in reviews if getattr(x, "section_code", None) == section_code), None
    )
    return r.internal_note if r else ""


@register.filter
def count_status(reviews, status):
    """Count reviews with a given status."""
    if isinstance(reviews, QuerySet):
        return reviews.filter(status=status).count()
    return sum(1 for r in reviews if getattr(r, "status", None) == status)


@register.filter
def count_not_reviewed(reviews, total):
    """Count sections that have no review yet (total minus reviewed, issue, and issue_solved)."""
    if isinstance(reviews, QuerySet):
        reviewed = reviews.filter(status="reviewed").count()
        issue = reviews.filter(status="issue").count()
        issue_solved = reviews.filter(status="issue_solved").count()
    else:
        reviewed = sum(1 for r in reviews if getattr(r, "status", None) == "reviewed")
        issue = sum(1 for r in reviews if getattr(r, "status", None) == "issue")
        issue_solved = sum(1 for r in reviews if getattr(r, "status", None) == "issue_solved")
    return total - reviewed - issue - issue_solved


@register.filter
def progress_pct(reviews, total):
    """Percentage of reviewed+issue+issue_solved sections."""
    if isinstance(reviews, QuerySet):
        done = reviews.filter(status__in=["reviewed", "issue", "issue_solved"]).count()
    else:
        done = sum(1 for r in reviews if getattr(r, "status", None) in ("reviewed", "issue", "issue_solved"))
    if not total:
        return 0
    return round(done / total * 100)


@register.filter
def section_findings(reviews):
    """Return only the issue-status reviews (findings)."""
    if isinstance(reviews, QuerySet):
        return reviews.filter(status="issue")
    return [r for r in reviews if getattr(r, "status", None) == "issue"]
