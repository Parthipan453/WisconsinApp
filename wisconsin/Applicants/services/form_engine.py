import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from django.db import models, transaction
from django.utils import timezone

from Applicants.models import (
    FormDefinition,
    FormSection,
    FormField,
    FieldChoice,
    ValidationRule,
    VisibilityRule,
    FormResponse,
    FieldResponse,
    FormAssignment,
    SectionAssignment,
    WorkflowDefinition,
    DynamicWorkflowStep,
    StepCondition,
    Application,
)


# =============================================================================
# REQUIREMENT RESOLVER
# =============================================================================


class RequirementResolver:
    """Resolves FormDefinitions, FormSections, WorkflowDefinitions, DocumentRequirements,
    and EssayPrompts for an application with explicit precedence rules.

    Precedence (highest to lowest):
      1. Exact match: program
      2. program + degree_level
      3. university + degree_level
      4. university
      5. degree_level
      6. applicant_category
      7. Global (all fields NULL/blank)

    Conflicting assignments at the same precedence level raise Conflict.
    """

    class Conflict(Exception):
        pass

    @staticmethod
    def _matcher_filter(assignment, application: Application) -> bool:
        """True when an assignment's scope matches the application.

        Works for both FormAssignment and SectionAssignment (same scope fields).
        """
        if assignment.university_id and assignment.university_id != application.university_id:
            return False
        if assignment.degree_level_id and assignment.degree_level_id != application.degree_level_id:
            return False
        if assignment.program_id and assignment.program_id != application.program_id:
            return False
        if assignment.applicant_type and assignment.applicant_type != (
            getattr(application, "applicant_category", None) or application.applicant_type
        ):
            return False
        return True

    @staticmethod
    def _precedence_score(obj, application: Application) -> int:
        uni = application.university_id
        dl = application.degree_level_id
        prog = application.program_id
        at = getattr(application, "applicant_category", None) or application.applicant_type

        get_uni = getattr(obj, "university_id", None) or getattr(obj, "university", None)
        if hasattr(get_uni, "pk"):
            get_uni = get_uni.pk
        get_dl = getattr(obj, "degree_level_id", None) or getattr(obj, "degree_level", None)
        if hasattr(get_dl, "pk"):
            get_dl = get_dl.pk
        get_prog = getattr(obj, "program_id", None) or getattr(obj, "program", None)
        if hasattr(get_prog, "pk"):
            get_prog = get_prog.pk
        get_at = getattr(obj, "applicant_type", None) or getattr(obj, "applicant_category", None)

        if get_prog and get_prog == prog:
            return 16
        if get_uni and get_dl and get_uni == uni and get_dl == dl:
            return 8
        if get_uni and get_uni == uni:
            return 4
        if get_dl and get_dl == dl:
            return 2
        if get_at and get_at == at:
            return 1
        return 0

    def resolve_forms(self, application: Application) -> list[FormDefinition]:
        assignments = FormAssignment.objects.filter(is_active=True).select_related("form")

        scored = []
        for a in assignments:
            if not self._matcher_filter(a, application):
                continue
            s = self._precedence_score(a, application)
            scored.append((s, a.sort_order, a.form))

        scored.sort(key=lambda x: (-x[0], x[1]))

        seen = set()
        result = []
        for _, _, form in scored:
            if form.pk not in seen:
                seen.add(form.pk)
                result.append(form)
        return result

    def is_section_allowed(self, application: Application, section: FormSection) -> bool:
        """A section is visible to an applicant when it has no active assignments
        (available to everyone) or when at least one of its active assignments matches
        the application's scope (university, degree level, applicant type, program)."""
        if not section.is_active:
            return False
        matching = list(
            SectionAssignment.objects.filter(section=section, is_active=True).only("pk", "university_id", "degree_level_id", "program_id", "applicant_type")
        )
        if not matching:
            return True
        return any(self._matcher_filter(a, application) for a in matching)

    def resolve_sections(
        self,
        application: Application,
        form: Optional[FormDefinition] = None,
    ) -> list[FormSection]:
        """Return the sections that should be shown for an application, optionally
        scoped to a single form. Sections without assignments default to visible."""
        qs = FormSection.objects.filter(is_active=True)
        assignment_qs = SectionAssignment.objects.filter(is_active=True)
        if form is not None:
            qs = qs.filter(form=form)
            assignment_qs = assignment_qs.filter(section__form=form)

        by_section: dict[int, list] = {}
        for a in assignment_qs.only(
            "section_id", "university_id", "degree_level_id",
            "program_id", "applicant_type",
        ):
            by_section.setdefault(a.section_id, []).append(a)

        visible = []
        for section in qs.select_related("form").order_by("form__sort_order", "sort_order"):
            sec_assignments = by_section.get(section.pk)
            if not sec_assignments or any(
                self._matcher_filter(a, application) for a in sec_assignments
            ):
                visible.append(section)
        return visible

    def resolve_workflow(self, application: Application) -> Optional[WorkflowDefinition]:
        workflows = WorkflowDefinition.objects.filter(is_active=True)

        scored = []
        for wf in workflows:
            if wf.university_id and wf.university_id != application.university_id:
                continue
            if wf.degree_level_id and wf.degree_level_id != application.degree_level_id:
                continue
            if wf.program_id and wf.program_id != application.program_id:
                continue
            if wf.applicant_type and wf.applicant_type != getattr(
                application, "applicant_category", application.applicant_type
            ):
                continue
            s = self._precedence_score(wf, application)
            scored.append((s, wf.is_default, wf.version, wf.pk, wf))

        if not scored:
            return None
        scored.sort(key=lambda x: (-x[0], -int(x[1]), -x[2], -x[3]))
        return scored[0][4]


# =============================================================================
# CONDITION EVALUATION
# =============================================================================


class ConditionEvaluator:
    """Evaluates StepCondition and VisibilityRule against an application context."""

    FIELD_MAPPING = {
        "applicant_type": lambda a: a.applicant_type,
        "applicant_category": lambda a: getattr(a, "applicant_category", None) or a.applicant_type,
        "admission_level": lambda a: getattr(a, "admission_level", None),
        "immigration_status": lambda a: getattr(a, "immigration_status", None),
        "degree_level": lambda a: a.degree_level_id,
        "university": lambda a: a.university_id,
        "program": lambda a: a.program_id,
        "military_status": lambda a: a.military_status,
        "residency_status": lambda a: a.residency_status,
    }

    OPERATORS = {
        "eq": lambda a, b: str(a) == str(b),
        "neq": lambda a, b: str(a) != str(b),
        "contains": lambda a, b: str(b) in str(a),
        "gt": lambda a, b: float(a or 0) > float(b),
        "gte": lambda a, b: float(a or 0) >= float(b),
        "lt": lambda a, b: float(a or 0) < float(b),
        "lte": lambda a, b: float(a or 0) <= float(b),
        "in": lambda a, b: str(a) in [x.strip() for x in str(b).split(",")],
        "not_in": lambda a, b: str(a) not in [x.strip() for x in str(b).split(",")],
        "is_empty": lambda a, b: not a,
        "not_empty": lambda a, b: bool(a),
        "checked": lambda a, b: bool(a),
        "not_checked": lambda a, b: not bool(a),
    }

    def resolve(
        self,
        condition,
        application: Application,
    ) -> tuple[Any, Any]:
        field_value = self._get_field_value(application, condition.target_field)
        compare_value = condition.value
        if isinstance(field_value, int):
            try:
                compare_value = int(compare_value)
            except (ValueError, TypeError):
                pass
        return field_value, compare_value

    def evaluate(
        self,
        condition,
        application: Application,
    ) -> bool:
        field_value, compare_value = self.resolve(condition, application)
        op_func = self.OPERATORS.get(condition.operator, lambda a, b: True)
        return op_func(field_value, compare_value)

    def evaluate_step_conditions(
        self,
        step: DynamicWorkflowStep,
        application: Application,
    ) -> bool:
        conditions = list(step.conditions.filter(is_active=True))
        if not conditions:
            return True

        and_conditions = [c for c in conditions if c.logic_operator == "AND"]
        or_conditions = [c for c in conditions if c.logic_operator == "OR"]

        for cond in and_conditions:
            if not self.evaluate(cond, application):
                return False

        if or_conditions:
            return any(self.evaluate(c, application) for c in or_conditions)
        return True

    def _get_field_value(self, application: Application, field_code: str) -> Any:
        resolver = self.FIELD_MAPPING.get(field_code)
        if resolver is None:
            return ""
        return resolver(application)


# =============================================================================
# DYNAMIC FORM ENGINE
# =============================================================================


class DynamicFormEngine:
    """Metadata-driven form engine with typed responses, snapshot, and workflow support."""

    def __init__(self) -> None:
        self.resolver = RequirementResolver()
        self.condition_evaluator = ConditionEvaluator()

    # ── Workflow & Form Resolution ────────────────────────────────────

    def get_forms_for_application(self, application: Application) -> list[FormDefinition]:
        return self.resolver.resolve_forms(application)

    def is_section_allowed(self, application: Application, section: FormSection) -> bool:
        return self.resolver.is_section_allowed(application, section)

    def get_workflow_for_application(self, application: Application) -> Optional[WorkflowDefinition]:
        return self.resolver.resolve_workflow(application)

    def get_active_workflow_steps(self, application: Application) -> list[DynamicWorkflowStep]:
        wf = self.get_workflow_for_application(application)
        if not wf:
            return []
        steps = DynamicWorkflowStep.objects.filter(
            workflow=wf, is_active=True,
        ).order_by("sort_order").prefetch_related("conditions")
        return [
            step for step in steps
            if self.condition_evaluator.evaluate_step_conditions(step, application)
        ]

    # ── Configuration Snapshot ────────────────────────────────────────

    def build_snapshot(self, application: Application) -> Optional[dict[str, Any]]:
        wf = self.get_workflow_for_application(application)
        if not wf:
            return None

        steps = self.get_active_workflow_steps(application)
        forms = self.get_forms_for_application(application)

        snapshot = {
            "workflow": {
                "id": wf.pk,
                "code": wf.code,
                "name": wf.name,
                "version": wf.version,
            },
            "steps": [],
            "forms": [],
            "snapshot_taken": timezone.now().isoformat(),
        }

        for step in steps:
            snapshot["steps"].append(
                {
                    "code": step.code,
                    "name": step.name,
                    "step_type": step.step_type,
                    "sort_order": step.sort_order,
                    "is_required": step.is_required,
                    "form_code": step.form.code if step.form else None,
                }
            )

        for form in forms:
            form_data = {
                "id": form.pk,
                "code": form.code,
                "name": form.name,
                "version": form.version,
                "sections": [],
            }
            for section in self.get_sections_for_application(application, form=form):
                section_data = {
                    "code": section.code,
                    "title": section.title,
                    "is_repeatable": section.is_repeatable,
                    "max_repeat": section.max_repeat,
                    "fields": [],
                }
                for field in FormField.objects.filter(
                    section=section, is_active=True
                ).order_by("sort_order"):
                    section_data["fields"].append(self._snapshot_field(field))
                form_data["sections"].append(section_data)
            snapshot["forms"].append(form_data)

        return snapshot

    @staticmethod
    def _snapshot_field(field: FormField) -> dict[str, Any]:
        choices = list(
            FieldChoice.objects.filter(field=field, is_active=True)
            .order_by("sort_order")
            .values("value", "label", "is_default")
        )
        validations = list(
            ValidationRule.objects.filter(field=field, is_active=True)
            .order_by("sort_order")
            .values("validation_type", "value", "value_max", "error_message")
        )
        return {
            "code": field.code,
            "label": field.label,
            "field_type": field.field_type,
            "layout_width": field.layout_width,
            "is_required": field.is_required,
            "is_readonly": field.is_readonly,
            "choices": choices,
            "validations": validations,
            "placeholder": field.placeholder,
            "help_text": field.help_text,
            "prefix_text": field.prefix_text,
            "suffix_text": field.suffix_text,
            "rows": field.rows,
            "max_file_size_mb": field.max_file_size_mb,
            "allowed_extensions": field.allowed_extensions,
        }

    # ── Form Building ─────────────────────────────────────────────────

    def get_sections_for_application(self, application: Application, form: Optional[FormDefinition] = None) -> list[FormSection]:
        return self.resolver.resolve_sections(application, form=form)

    def build_form_context(
        self,
        section: FormSection,
        application: Application,
        response: Optional[FormResponse] = None,
    ) -> dict[str, Any]:
        fields = FormField.objects.filter(
            section=section, is_active=True,
        ).order_by("sort_order").prefetch_related("choices", "validations")

        field_data = []
        for field in fields:
            choices = list(field.choices.filter(is_active=True).order_by("sort_order"))
            validations = list(field.validations.filter(is_active=True).order_by("sort_order"))
            visibility = list(
                VisibilityRule.objects.filter(field=field, is_active=True).order_by("sort_order")
            )

            existing_value = None
            existing_file = None
            if response:
                try:
                    fr = response.field_responses.get(field=field)
                    existing_value = fr.typed_value()
                    if field.field_type == "year" and existing_value:
                        existing_value = str(existing_value)
                    existing_file = fr.file if fr.file else None
                except FieldResponse.DoesNotExist:
                    pass

            field_data.append(
                {
                    "field": field,
                    "choices": choices,
                    "validations": validations,
                    "visibility": visibility,
                    "value": existing_value if existing_value is not None else field.default_value,
                    "file": existing_file,
                    "is_required": field.is_required,
                }
            )

        return {
            "section": section,
            "fields": field_data,
            "response": response,
            "repeat_index": response.repeat_index if response else 0,
        }

    # ── Typed Response Handling ───────────────────────────────────────

    def get_or_create_response(
        self,
        application: Application,
        section: FormSection,
        repeat_index: int = 0,
    ) -> FormResponse:
        response, _ = FormResponse.objects.get_or_create(
            application=application,
            section=section,
            repeat_index=repeat_index,
            defaults={"form": section.form},
        )
        return response

    def save_field_responses(
        self,
        section: FormSection,
        response: FormResponse,
        cleaned_data: dict[str, Any],
        mark_complete: bool = True,
    ) -> None:
        fields = {
            f.code: f
            for f in FormField.objects.filter(section=section, is_active=True)
        }

        for code, value in cleaned_data.items():
            field = fields.get(code)
            if not field:
                continue

            kwargs = self._build_field_kwargs(field, value)
            FieldResponse.objects.update_or_create(
                response=response,
                field=field,
                defaults=kwargs,
            )

        if mark_complete:
            response.is_complete = True
            response.completed_at = timezone.now()
        response.save()

    @staticmethod
    def _build_field_kwargs(field: FormField, value: Any) -> dict[str, Any]:
        kwargs = {}
        if field.field_type == "file":
            kwargs["file"] = str(value) if value else ""
            kwargs["file_name"] = getattr(value, "name", "") if value else ""
            kwargs["value"] = str(value) if value else ""
        elif field.field_type in ("number", "gpa", "currency"):
            kwargs["value_numeric"] = float(value) if value not in (None, "", "0") else 0.0
            kwargs["value"] = str(value) if value is not None else ""
        elif field.field_type == "year":
            kwargs["value"] = str(value) if value not in (None, "") else ""
        elif field.field_type in ("multi_select",) or isinstance(value, list):
            kwargs["value_json"] = json.dumps(value) if value else "[]"
            kwargs["value"] = json.dumps(value) if value else "[]"
        elif isinstance(value, bool) or field.field_type == "checkbox":
            kwargs["value_bool"] = bool(value)
            kwargs["value"] = "on" if value else "off"
        elif field.is_encrypted:
            from django.core.signing import Signer
            signer = Signer()
            kwargs["value_encrypted"] = signer.sign(str(value)) if value else ""
            kwargs["value"] = ""
        else:
            kwargs["value"] = str(value) if value is not None else ""
        return kwargs

    def get_all_application_data(self, application: Application) -> dict[str, Any]:
        responses = FormResponse.objects.filter(application=application).select_related(
            "section", "section__form"
        ).prefetch_related("field_responses", "field_responses__field")

        data = {}
        for resp in responses:
            section_data = []
            for fr in resp.field_responses.all():
                section_data.append(
                    {
                        "field_code": fr.field.code,
                        "field_label": fr.field.label,
                        "field_type": fr.field.field_type,
                        "value": fr.typed_value(),
                        "file": fr.file,
                        "file_name": fr.file_name,
                    }
                )

            key = f"{resp.section.form.code}_{resp.section.code}"
            if resp.repeat_index:
                key += f"_{resp.repeat_index}"
            data[key] = {
                "form": resp.section.form.name,
                "section": resp.section.title,
                "repeat_index": resp.repeat_index,
                "fields": section_data,
                "is_complete": resp.is_complete,
            }
        return data

    # ── Progress ──────────────────────────────────────────────────────

    def calculate_progress(self, application: Application) -> int:
        steps = self.get_active_workflow_steps(application)
        if not steps:
            return 0

        form_steps = [s for s in steps if s.step_type == "form" and s.form]
        if not form_steps:
            return 0

        total = 0
        completed = 0
        for step in form_steps:
            sections = self.get_sections_for_application(application, form=step.form)
            total += len(sections)
            completed += FormResponse.objects.filter(
                application=application,
                section__in=sections,
                is_complete=True,
            ).count()

        if total == 0:
            return 0
        return int((completed / total) * 100)

    def is_step_complete(self, application: Application, step_code: str) -> bool:
        steps = self.get_active_workflow_steps(application)
        step = next((s for s in steps if s.code == step_code), None)
        if not step:
            return False

        if step.step_type != "form" or not step.form:
            return all(
                not (fs.step_type == "form" and fs.form and fs.is_required)
                or self._is_form_step_complete(application, fs)
                for fs in steps
            )
        return self._is_form_step_complete(application, step)

    @staticmethod
    def _is_form_step_complete(application: Application, step: DynamicWorkflowStep) -> bool:
        engine = DynamicFormEngine()
        sections = engine.get_sections_for_application(application, form=step.form)
        if not sections:
            return True
        completed = FormResponse.objects.filter(
            application=application,
            section__in=sections,
            is_complete=True,
        ).count()
        return completed >= len(sections)

    # ── Validation ────────────────────────────────────────────────────

    def validate_field(self, field: FormField, value: Any) -> tuple[bool, str]:
        rules = ValidationRule.objects.filter(
            field=field, is_active=True
        ).order_by("sort_order")
        for rule in rules:
            is_valid, msg = self._apply_rule(rule, value)
            if not is_valid:
                return False, msg or rule.error_message or f"Invalid value for {field.label}"
        return True, ""

    @staticmethod
    def _apply_rule(rule: ValidationRule, value: Any) -> tuple[bool, str]:
        if rule.validation_type == "required":
            if not value or (isinstance(value, str) and not value.strip()):
                return False, "This field is required."
        elif rule.validation_type == "min_length":
            if value and len(str(value)) < int(rule.value):
                return False, f"Minimum {rule.value} characters required."
        elif rule.validation_type == "max_length":
            if value and len(str(value)) > int(rule.value):
                return False, f"Maximum {rule.value} characters allowed."
        elif rule.validation_type == "min_value":
            if value is not None and value != "":
                try:
                    if float(value) < float(rule.value):
                        return False, f"Minimum value is {rule.value}."
                except (ValueError, TypeError):
                    try:
                        from datetime import date as dt_date
                        if hasattr(value, "isoformat") and hasattr(dt_date, "fromisoformat"):
                            v = dt_date.fromisoformat(str(value)) if isinstance(value, str) else value
                            r = dt_date.fromisoformat(str(rule.value))
                            if v < r:
                                return False, f"Minimum date is {rule.value}."
                    except (ValueError, TypeError):
                        pass
        elif rule.validation_type == "max_value":
            if value is not None and value != "":
                try:
                    if float(value) > float(rule.value):
                        return False, f"Maximum value is {rule.value}."
                except (ValueError, TypeError):
                    try:
                        from datetime import date as dt_date
                        if hasattr(value, "isoformat") and hasattr(dt_date, "fromisoformat"):
                            v = dt_date.fromisoformat(str(value)) if isinstance(value, str) else value
                            r = dt_date.fromisoformat(str(rule.value))
                            if v > r:
                                return False, f"Maximum date is {rule.value}."
                    except (ValueError, TypeError):
                        pass
        elif rule.validation_type == "regex":
            if value and not re.match(rule.value, str(value)):
                return False, rule.error_message or "Invalid format."
        elif rule.validation_type == "email":
            if value and not re.match(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                str(value),
            ):
                return False, "Invalid email address."
        elif rule.validation_type == "phone":
            if value:
                cleaned = re.sub(r"[\s\-\(\)\.]", "", str(value))
                if not re.match(r"^\+?\d{7,15}$", cleaned):
                    return False, "Enter a valid phone number with country code (e.g. +1234567890)."
        elif rule.validation_type == "word_count":
            if value:
                wc = len(str(value).split())
                min_w = int(rule.value or 0)
                max_w = int(rule.value_max or 99999)
                if wc < min_w:
                    return False, f"Minimum {min_w} words required."
                if wc > max_w:
                    return False, f"Maximum {max_w} words allowed."
        return True, ""
