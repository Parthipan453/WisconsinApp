import json
import re as _re
from functools import wraps

from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from Applicants.models import (
    FormDefinition,
    FormSection,
    FormField,
    FieldChoice,
    ValidationRule,
    VisibilityRule,
    FormAssignment,
    SectionAssignment,
    WorkflowDefinition,
    DynamicWorkflowStep,
    StepCondition,
    AdmissionCycle,
    Application,
    ApplicationFee,
    ApplicantTypeRequirement,
    DocumentRequirement,
    DOCUMENT_CATEGORY_CHOICES,
)
from Admin.Colleges.models import University, Degree, AcademicProgram


 

def _admin_required(view):
    @wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Login required.")
            return redirect("/accounts/login/")
        return view(request, *args, **kwargs)
    return wrapper


def _int_or(value, default):
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


 

@_admin_required
def dashboard(request: HttpRequest) -> HttpResponse:
    forms = FormDefinition.objects.all().order_by("sort_order")
    form_data = []
    for form in forms:
        sections = form.sections.filter(is_active=True)
        total_fields = FormField.objects.filter(
            section__in=sections, is_active=True
        ).count()
        assignments = form.assignments.filter(is_active=True).count()
        form_data.append(
            {
                "form": form,
                "section_count": sections.count(),
                "field_count": total_fields,
                "assignment_count": assignments,
            }
        )
    workflows = WorkflowDefinition.objects.all().order_by("code")
    cycles = AdmissionCycle.objects.all().order_by("-application_start")
    return render(
        request,
        "Applicants/builder/dashboard.html",
        {
            "form_data": form_data,
            "workflows": workflows,
            "cycles": cycles,
            "total_forms": forms.count(),
            "total_workflows": workflows.count(),
            "total_fees": ApplicationFee.objects.count(),
            "total_req_types": ApplicantTypeRequirement.objects.count(),
            "total_doc_reqs": DocumentRequirement.objects.count(),
        },
    )


 

@_admin_required
def form_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        if not code or not name:
            messages.error(request, "Code and Name are required.")
            return redirect("builder_form_create")
        form = FormDefinition.objects.create(
            code=code,
            name=name,
            description=request.POST.get("description", ""),
            icon=request.POST.get("icon", ""),
            sort_order=request.POST.get("sort_order", 0),
        )
        messages.success(request, f"Form '{name}' created.")
        return redirect(f"/applicants/builder/forms/{form.pk}/edit/")
    return render(request, "Applicants/builder/form_create.html")


@_admin_required
def form_edit(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    if request.method == "POST":
        form_def.name = request.POST.get("name", form_def.name)
        form_def.description = request.POST.get("description", "")
        form_def.icon = request.POST.get("icon", "")
        form_def.sort_order = int(request.POST.get("sort_order", 0))
        form_def.is_active = request.POST.get("is_active") == "on"
        form_def.version = (form_def.version or 1) + 1
        form_def.save()
        messages.success(request, "Form updated.")
        return redirect(f"/applicants/builder/forms/{form_id}/edit/")

    sections = (
        form_def.sections.filter(is_active=True)
        .order_by("sort_order")
        .prefetch_related(
            Prefetch(
                "fields",
                queryset=FormField.objects.filter(is_active=True).order_by("sort_order"),
            )
        )
    )
    all_fields = FormField.objects.filter(section__form=form_def, is_active=True)
    logic_rules = VisibilityRule.objects.filter(
        field__section__form=form_def, is_active=True
    ).select_related("field", "target_field").order_by("field__sort_order", "sort_order")

    preview_sections = _build_form_preview_sections(form_def)
    return render(
        request,
        "Applicants/builder/form_edit.html",
        {
            "form_def": form_def,
            "sections": sections,
            "preview_sections": preview_sections,
            "field_types": FormField._meta.get_field("field_type").choices,
            "layout_widths": FormField._meta.get_field("layout_width").choices,
            "logic_rules": logic_rules,
            "all_fields": all_fields,
        },
    )


@_admin_required
def form_delete(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    if request.method == "POST":
        name = form_def.name
        form_def.delete()
        messages.success(request, f"Form '{name}' deleted.")
        return redirect("/applicants/builder/")
    return render(
        request, "Applicants/builder/form_delete.html", {"form_def": form_def}
    )


@_admin_required
def form_clone(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    new_form = _deep_clone_form(form_def)
    messages.success(request, f"Form cloned as '{new_form.name}'.")
    return redirect(f"/applicants/builder/forms/{new_form.pk}/edit/")


def _deep_clone_form(form_def: FormDefinition) -> FormDefinition:
    new_form = FormDefinition.objects.create(
        code=form_def.code + "_copy",
        name=form_def.name + " (Copy)",
        description=form_def.description,
        icon=form_def.icon,
        sort_order=form_def.sort_order + 1,
    )
    for section in form_def.sections.filter(is_active=True).order_by("sort_order"):
        new_section = FormSection.objects.create(
            form=new_form,
            code=section.code,
            title=section.title,
            description=section.description,
            help_text=section.help_text,
            sort_order=section.sort_order,
            is_repeatable=section.is_repeatable,
            max_repeat=section.max_repeat,
            render_as=section.render_as,
        )
        _clone_section_assignments(section, new_section)
        for field in FormField.objects.filter(
            section=section, is_active=True
        ).order_by("sort_order"):
            _clone_field(field, new_section)
    return new_form


def _clone_section_assignments(source: FormSection, new_section: FormSection) -> None:
    for a in SectionAssignment.objects.filter(section=source, is_active=True).order_by("sort_order"):
        SectionAssignment.objects.create(
            section=new_section,
            university_id=a.university_id,
            degree_level_id=a.degree_level_id,
            applicant_type=a.applicant_type,
            program_id=a.program_id,
            school_id=a.school_id,
            sort_order=a.sort_order,
            is_required=a.is_required,
        )


def _clone_field(field: FormField, new_section: FormSection) -> None:
    new_field = FormField.objects.create(
        section=new_section,
        code=field.code,
        label=field.label,
        placeholder=field.placeholder,
        help_text=field.help_text,
        field_type=field.field_type,
        default_value=field.default_value,
        sort_order=field.sort_order,
        css_class=field.css_class,
        layout_width=field.layout_width,
        rows=field.rows,
        max_file_size_mb=field.max_file_size_mb,
        allowed_extensions=field.allowed_extensions,
        data_source=field.data_source,
        is_required=field.is_required,
        is_readonly=field.is_readonly,
        is_encrypted=field.is_encrypted,
        is_visible=getattr(field, "is_visible", True),
        regex_pattern=getattr(field, "regex_pattern", "") or "",
        min_length=getattr(field, "min_length", None),
        max_length=getattr(field, "max_length", None),
    )
    for choice in FieldChoice.objects.filter(
        field=field, is_active=True
    ).order_by("sort_order"):
        FieldChoice.objects.create(
            field=new_field,
            value=choice.value,
            label=choice.label,
            sort_order=choice.sort_order,
            is_default=choice.is_default,
        )
    for rule in ValidationRule.objects.filter(
        field=field, is_active=True
    ).order_by("sort_order"):
        ValidationRule.objects.create(
            field=new_field,
            validation_type=rule.validation_type,
            value=rule.value,
            value_max=rule.value_max,
            error_message=rule.error_message,
            sort_order=rule.sort_order,
        )
    for vis in VisibilityRule.objects.filter(
        field=field, is_active=True
    ).order_by("sort_order"):
        VisibilityRule.objects.create(
            field=new_field,
            target_field=vis.target_field,
            operator=vis.operator,
            value=vis.value,
            logic_operator=vis.logic_operator,
            sort_order=vis.sort_order,
            action=vis.action,
        )


 

@_admin_required
def section_add(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        code = request.POST.get("code", "").strip()
        if not code and title:
            code = _re.sub(r"[^a-z0-9]+", "_", title.lower().strip())[:50].strip("_")
        if not code or not title:
            messages.error(request, "Code and Title are required.")
            return redirect(f"/applicants/builder/forms/{form_id}/edit/")
        base_code = code
        n = 1
        while form_def.sections.filter(code=code).exists():
            code = f"{base_code}_{n}"
            n += 1
        last = (
            form_def.sections.filter(is_active=True)
            .order_by("-sort_order")
            .first()
        )
        sort_order = int(request.POST.get("sort_order", 0)) or (
            last.sort_order + 1 if last else 1
        )
        FormSection.objects.create(
            form=form_def,
            code=code,
            title=title,
            description=request.POST.get("description", ""),
            sort_order=sort_order,
            is_repeatable=request.POST.get("is_repeatable") == "on",
            max_repeat=int(request.POST.get("max_repeat", 1)),
            render_as=request.POST.get("render_as", "card"),
        )
        messages.success(request, f"Section '{title}' added.")
    return redirect(f"/applicants/builder/forms/{form_id}/edit/")


@_admin_required
def section_clone(request: HttpRequest, section_id: int) -> HttpResponse:
    section = get_object_or_404(FormSection, pk=section_id)
    form_id = section.form_id
    orig_code = section.code
    new_code = orig_code + "_copy"
    n = 1
    while section.form.sections.filter(code=new_code).exists():
        new_code = f"{orig_code}_copy{n}"
        n += 1
    new_section = FormSection.objects.create(
        form=section.form,
        code=new_code,
        title=section.title + " (Copy)",
        description=section.description,
        help_text=section.help_text,
        sort_order=section.sort_order + 1,
        is_repeatable=section.is_repeatable,
        max_repeat=section.max_repeat,
        render_as=section.render_as,
    )
    for field in FormField.objects.filter(
        section=section, is_active=True
    ).order_by("sort_order"):
        _clone_field(field, new_section)
    _clone_section_assignments(section, new_section)
    messages.success(request, f"Section '{section.title}' duplicated.")
    return redirect(f"/applicants/builder/forms/{form_id}/edit/")


@_admin_required
def section_edit(request: HttpRequest, section_id: int) -> HttpResponse:
    section = get_object_or_404(FormSection, pk=section_id)
    if request.method == "POST":
        section.title = request.POST.get("title", section.title)
        section.description = request.POST.get("description", "")
        section.help_text = request.POST.get("help_text", "")
        section.sort_order = _int_or(request.POST.get("sort_order"), section.sort_order)
        section.is_repeatable = request.POST.get("is_repeatable") == "on"
        section.max_repeat = _int_or(request.POST.get("max_repeat"), 1)
        section.render_as = request.POST.get("render_as", "card")
        section.is_active = request.POST.get("is_active") == "on"
        section.save()
        messages.success(request, "Section updated.")
    return redirect(f"/applicants/builder/forms/{section.form_id}/edit/")


@_admin_required
def section_delete(request: HttpRequest, section_id: int) -> HttpResponse:
    section = get_object_or_404(FormSection, pk=section_id)
    form_id = section.form_id
    if request.method == "POST":
        section.delete()
        messages.success(request, "Section deleted.")
        return redirect(f"/applicants/builder/forms/{form_id}/edit/")
    return render(
        request,
        "Applicants/builder/section_delete.html",
        {"section": section},
    )


# ─── Field CRUD ────────────────────────────────────────────────────────


@_admin_required
def field_add_form(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    if request.method == "POST":
        section_id = request.POST.get("section_id")
        if not section_id:
            messages.error(request, "Section is required.")
            return redirect(f"/applicants/builder/forms/{form_id}/edit/")
        section = get_object_or_404(FormSection, pk=section_id, form=form_def)
        code = request.POST.get("code", "").strip()
        label = request.POST.get("label", "").strip()
        if not label:
            ft = request.POST.get("field_type", "text")
            count = FormField.objects.filter(section=section).count() + 1
            label = f"{ft.title()} Field {count}"
        if not code:
            code = _re.sub(r"[^a-z0-9]+", "_", label.lower().strip())[:50].strip("_")
        base_code = code
        n = 1
        while FormField.objects.filter(section=section, code=code).exists():
            code = f"{base_code}_{n}"
            n += 1
        last = (
            FormField.objects.filter(section=section)
            .order_by("-sort_order")
            .first()
        )
        sort_order = _int_or(request.POST.get("sort_order"), 0) or (
            last.sort_order + 1 if last else 1
        )
        FormField.objects.create(
            section=section,
            code=code,
            label=label,
            field_type=request.POST.get("field_type", "text"),
            placeholder=request.POST.get("placeholder", ""),
            help_text=request.POST.get("help_text", ""),
            layout_width=request.POST.get("layout_width", "full"),
            sort_order=sort_order,
            is_required=request.POST.get("is_required") == "on",
            is_active=request.POST.get("is_active", "on") != "off",
            is_visible=request.POST.get("is_visible", "on") != "off",
            is_readonly=request.POST.get("is_readonly") == "on",
            is_encrypted=request.POST.get("is_encrypted") == "on",
            rows=_int_or(request.POST.get("rows"), 4),
            prefix_text=request.POST.get("prefix_text", ""),
            suffix_text=request.POST.get("suffix_text", ""),
            default_value=request.POST.get("default_value", ""),
            regex_pattern=(
                request.POST.get("custom_regex", "").strip()
                if request.POST.get("regex_pattern", "").strip() == "custom"
                else request.POST.get("regex_pattern", "").strip()
            ),
            min_length=_int_or(request.POST.get("min_length"), None),
            max_length=_int_or(request.POST.get("max_length"), None),
            max_file_size_mb=_int_or(request.POST.get("max_file_size_mb"), 10),
            allowed_extensions=request.POST.get(
                "allowed_extensions", ".pdf,.doc,.docx,.jpg,.png"
            ),
            data_source=request.POST.get("data_source", ""),
            label_color=request.POST.get("label_color", ""),
            input_color=request.POST.get("input_color", ""),
            font_size=request.POST.get("font_size", ""),
            input_background=request.POST.get("input_background", ""),
            border_color=request.POST.get("border_color", ""),
            input_height=request.POST.get("input_height", ""),
        )
        # Persist choices (value | Label) submitted with the create form
        choices_raw = request.POST.get("choices", "").strip()
        if choices_raw:
            new_field = FormField.objects.filter(
                section=section, code=code
            ).order_by("-pk").first()
            for idx, line in enumerate(choices_raw.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    val, lbl = [p.strip() for p in line.split("|", 1)]
                else:
                    val, lbl = line, line
                if not val:
                    continue
                FieldChoice.objects.create(
                    field=new_field,
                    value=val,
                    label=lbl,
                    sort_order=idx,
                )
        messages.success(request, f"Field '{label}' added.")
    return redirect(f"/applicants/builder/forms/{form_id}/edit/")


@_admin_required
def field_clone(request: HttpRequest, field_id: int) -> HttpResponse:
    field = get_object_or_404(FormField, pk=field_id)
    section = field.section
    orig_code = field.code
    new_code = orig_code + "_copy"
    n = 1
    while FormField.objects.filter(section=section, code=new_code).exists():
        new_code = f"{orig_code}_copy{n}"
        n += 1
    field.code = new_code
    field.label = field.label + " (Copy)"
    _clone_field(field, section)
    messages.success(request, f"Field '{field.label}' duplicated.")
    return redirect(f"/applicants/builder/forms/{section.form_id}/edit/")


def _sync_validation_rules(field: FormField, post_data) -> None:
    """Create/update/delete ValidationRule records to match sidebar values."""
    # --- required ---
    is_required = post_data.get("is_required") == "on"
    req_rule, created = ValidationRule.objects.get_or_create(
        field=field, validation_type="required", defaults={"is_active": is_required},
    )
    if not created:
        req_rule.is_active = is_required
        req_rule.save()

    # --- regex ---
    regex_val = post_data.get("regex_pattern", "").strip()
    if regex_val == "custom":
        regex_val = post_data.get("custom_regex", "").strip() or ""
    regex_rule, created = ValidationRule.objects.get_or_create(
        field=field, validation_type="regex",
        defaults={"value": regex_val, "is_active": bool(regex_val)},
    )
    if not created:
        regex_rule.value = regex_val
        regex_rule.is_active = bool(regex_val)
        regex_rule.save()

    # --- max_length ---
    xl = post_data.get("max_length", "").strip()
    if xl:
        ml_rule, created = ValidationRule.objects.get_or_create(
            field=field, validation_type="max_length",
            defaults={"value": xl, "is_active": True},
        )
        if not created:
            ml_rule.value = xl
            ml_rule.is_active = True
            ml_rule.save()
    else:
        ValidationRule.objects.filter(
            field=field, validation_type="max_length"
        ).update(is_active=False)

    # --- min_length ---
    mnl = post_data.get("min_length", "").strip()
    if mnl:
        mnl_rule, created = ValidationRule.objects.get_or_create(
            field=field, validation_type="min_length",
            defaults={"value": mnl, "is_active": True},
        )
        if not created:
            mnl_rule.value = mnl
            mnl_rule.is_active = True
            mnl_rule.save()
    else:
        ValidationRule.objects.filter(
            field=field, validation_type="min_length"
        ).update(is_active=False)


@_admin_required
def field_edit(request: HttpRequest, field_id: int) -> HttpResponse:
    field = get_object_or_404(FormField, pk=field_id)
    if request.method == "POST":
        field.code = request.POST.get("code", field.code)
        field.label = request.POST.get("label", field.label)
        field.placeholder = request.POST.get("placeholder", "")
        field.help_text = request.POST.get("help_text", "")
        field.field_type = request.POST.get("field_type", field.field_type)
        field.default_value = request.POST.get("default_value", "")
        field.sort_order = _int_or(request.POST.get("sort_order"), field.sort_order)
        field.layout_width = request.POST.get("layout_width", "full")
        field.css_class = request.POST.get("css_class", "")
        field.rows = _int_or(request.POST.get("rows"), 4)
        field.prefix_text = request.POST.get("prefix_text", "")
        field.suffix_text = request.POST.get("suffix_text", "")
        field.is_required = request.POST.get("is_required") == "on"
        field.is_readonly = request.POST.get("is_readonly") == "on"
        field.is_encrypted = request.POST.get("is_encrypted") == "on"
        field.is_active = request.POST.get("is_active") == "on"
        field.is_visible = request.POST.get("is_visible", "on") != "off"
        pattern = request.POST.get("regex_pattern", "").strip()
        if pattern == "custom":
            pattern = request.POST.get("custom_regex", "").strip() or ""
        field.regex_pattern = pattern
        ml = request.POST.get("min_length", "")
        field.min_length = int(ml) if ml else None
        xl = request.POST.get("max_length", "")
        field.max_length = int(xl) if xl else None
        field.max_file_size_mb = _int_or(request.POST.get("max_file_size_mb"), 10)
        field.allowed_extensions = request.POST.get(
            "allowed_extensions", ".pdf,.doc,.docx,.jpg,.png"
        )
        field.data_source = request.POST.get("data_source", "")
        field.label_color = request.POST.get("label_color", "")
        field.input_color = request.POST.get("input_color", "")
        field.font_size = request.POST.get("font_size", "")
        field.input_background = request.POST.get("input_background", "")
        field.border_color = request.POST.get("border_color", "")
        field.input_height = request.POST.get("input_height", "")
        field.save()

        # Sync ValidationRule records so the applicant form actually enforces these
        _sync_validation_rules(field, request.POST)

        # Sync choices from the sidebar "value | Label" textarea
        choices_raw = request.POST.get("choices", "").strip()
        if choices_raw:
            submitted = []
            for idx, line in enumerate(choices_raw.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    val, lbl = [p.strip() for p in line.split("|", 1)]
                else:
                    val, lbl = line, line
                if not val:
                    continue
                submitted.append(val)
                FieldChoice.objects.update_or_create(
                    field=field, value=val,
                    defaults={"label": lbl, "sort_order": idx, "is_active": True},
                )
            FieldChoice.objects.filter(field=field).exclude(
                value__in=submitted
            ).update(is_active=False)

        messages.success(request, "Field updated.")
        return redirect(f"/applicants/builder/forms/{field.section.form_id}/edit/")

    choices = FieldChoice.objects.filter(field=field, is_active=True).order_by(
        "sort_order"
    )
    validations = ValidationRule.objects.filter(
        field=field, is_active=True
    ).order_by("sort_order")
    visibility_rules = VisibilityRule.objects.filter(
        field=field, is_active=True
    ).order_by("sort_order")
    all_fields = (
        FormField.objects.filter(section=field.section, is_active=True)
        .exclude(pk=field.pk)
        .order_by("sort_order")
    )

    return render(
        request,
        "Applicants/builder/field_edit.html",
        {
            "field": field,
            "choices": choices,
            "validations": validations,
            "visibility_rules": visibility_rules,
            "all_fields": all_fields,
            "field_types": FormField._meta.get_field("field_type").choices,
            "layout_widths": FormField._meta.get_field("layout_width").choices,
            "validation_types": ValidationRule._meta.get_field(
                "validation_type"
            ).choices,
            "visibility_operators": VisibilityRule._meta.get_field(
                "operator"
            ).choices,
            "logic_operators": VisibilityRule._meta.get_field(
                "logic_operator"
            ).choices,
        },
    )


@_admin_required
def field_json(request: HttpRequest, field_id: int) -> HttpResponse:
    from django.http import JsonResponse
    field = get_object_or_404(FormField, pk=field_id)
    choices_qs = FieldChoice.objects.filter(field=field, is_active=True).order_by(
        "sort_order"
    )
    choices_list = [f"{c.value} | {c.label}" for c in choices_qs]
    # Read validation from ValidationRule (the source of truth for applicant forms)
    vrules = ValidationRule.objects.filter(field=field, is_active=True)
    regex_rule = vrules.filter(validation_type="regex").first()
    ml_rule = vrules.filter(validation_type="max_length").first()
    mnl_rule = vrules.filter(validation_type="min_length").first()
    return JsonResponse({
        "pk": field.pk,
        "code": field.code,
        "label": field.label,
        "field_type": field.field_type,
        "placeholder": field.placeholder or "",
        "help_text": field.help_text or "",
        "default_value": field.default_value or "",
        "is_required": field.is_required,
        "is_visible": getattr(field, "is_visible", True),
        "is_active": field.is_active,
        "is_readonly": field.is_readonly,
        "is_encrypted": field.is_encrypted,
        "regex_pattern": regex_rule.value if regex_rule and regex_rule.value else "",
        "min_length": mnl_rule.value if mnl_rule and mnl_rule.value else "",
        "max_length": ml_rule.value if ml_rule and ml_rule.value else "",
        "choices": "\n".join(choices_list),
        "sort_order": field.sort_order,
        "layout_width": field.layout_width,
        "prefix_text": field.prefix_text or "",
        "suffix_text": field.suffix_text or "",
        "rows": field.rows,
        "max_file_size_mb": field.max_file_size_mb,
        "allowed_extensions": field.allowed_extensions or "",
        "data_source": field.data_source or "",
        "label_color": field.label_color or "",
        "input_color": field.input_color or "",
        "font_size": field.font_size or "",
        "input_background": field.input_background or "",
        "border_color": field.border_color or "",
        "input_height": field.input_height or "",
        "css_class": field.css_class or "",
    })


@_admin_required
def section_json(request: HttpRequest, section_id: int) -> HttpResponse:
    from django.http import JsonResponse
    section = get_object_or_404(FormSection, pk=section_id)
    return JsonResponse({
        "pk": section.pk,
        "code": section.code,
        "title": section.title,
        "description": section.description or "",
        "help_text": section.help_text or "",
        "sort_order": section.sort_order,
        "is_repeatable": section.is_repeatable,
        "max_repeat": section.max_repeat,
        "render_as": section.render_as,
        "is_active": section.is_active,
        "start_hidden": getattr(section, "start_hidden", False),
    })


@_admin_required
def form_json(request: HttpRequest, form_id: int) -> HttpResponse:
    from django.http import JsonResponse
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    return JsonResponse({
        "pk": form_def.pk,
        "code": form_def.code,
        "name": form_def.name,
        "description": form_def.description or "",
        "icon": form_def.icon or "",
        "sort_order": form_def.sort_order,
        "is_active": form_def.is_active,
        "version": form_def.version,
    })


@_admin_required
def field_delete(request: HttpRequest, field_id: int) -> HttpResponse:
    field = get_object_or_404(FormField, pk=field_id)
    form_id = field.section.form_id
    if request.method == "POST":
        field.delete()
        messages.success(request, "Field deleted.")
        return redirect(f"/applicants/builder/forms/{form_id}/edit/")
    return render(
        request, "Applicants/builder/field_delete.html", {"field": field}
    )


# ─── Field Choices ─────────────────────────────────────────────────────


@_admin_required
def choice_add(request: HttpRequest, field_id: int) -> HttpResponse:
    field = get_object_or_404(FormField, pk=field_id)
    if request.method == "POST":
        value = request.POST.get("value", "").strip()
        label = request.POST.get("label", "").strip()
        if value and label:
            FieldChoice.objects.create(
                field=field,
                value=value,
                label=label,
                sort_order=int(request.POST.get("sort_order", 0)),
                is_default=request.POST.get("is_default") == "on",
            )
            messages.success(request, "Choice added.")
        else:
            messages.error(request, "Value and Label are required.")
    return redirect(f"/applicants/builder/fields/{field_id}/edit/")


@_admin_required
def choice_delete(request: HttpRequest, choice_id: int) -> HttpResponse:
    choice = get_object_or_404(FieldChoice, pk=choice_id)
    field_id = choice.field_id
    if request.method == "POST":
        choice.delete()
        messages.success(request, "Choice deleted.")
    return redirect(f"/applicants/builder/fields/{field_id}/edit/")


# ─── Validation Rules ──────────────────────────────────────────────────


@_admin_required
def validation_add(request: HttpRequest, field_id: int) -> HttpResponse:
    field = get_object_or_404(FormField, pk=field_id)
    if request.method == "POST":
        validation_type = request.POST.get("validation_type", "")
        if validation_type:
            ValidationRule.objects.create(
                field=field,
                validation_type=validation_type,
                value=request.POST.get("value", ""),
                value_max=request.POST.get("value_max", ""),
                error_message=request.POST.get("error_message", ""),
                sort_order=int(request.POST.get("sort_order", 0)),
            )
            messages.success(request, "Validation rule added.")
    return redirect(f"/applicants/builder/fields/{field_id}/edit/")


@_admin_required
def validation_delete(
    request: HttpRequest, validation_id: int
) -> HttpResponse:
    rule = get_object_or_404(ValidationRule, pk=validation_id)
    field_id = rule.field_id
    if request.method == "POST":
        rule.delete()
        messages.success(request, "Validation rule deleted.")
    return redirect(f"/applicants/builder/fields/{field_id}/edit/")


# ─── Visibility Rules ──────────────────────────────────────────────────


@_admin_required
def visibility_add(request: HttpRequest, field_id: int) -> HttpResponse:
    field = get_object_or_404(FormField, pk=field_id)
    if request.method == "POST":
        target_id = request.POST.get("target_field")
        operator = request.POST.get("operator", "eq")
        value = request.POST.get("value", "")
        if target_id:
            VisibilityRule.objects.create(
                field=field,
                target_field_id=target_id,
                operator=operator,
                value=value,
                logic_operator=request.POST.get("logic_operator", "AND"),
                sort_order=int(request.POST.get("sort_order", 0)),
                action=request.POST.get("action", "show"),
            )
            messages.success(request, "Visibility rule added.")
    return redirect(f"/applicants/builder/fields/{field_id}/edit/")


@_admin_required
def visibility_delete(
    request: HttpRequest, visibility_id: int
) -> HttpResponse:
    rule = get_object_or_404(VisibilityRule, pk=visibility_id)
    field_id = rule.field_id
    if request.method == "POST":
        rule.delete()
        messages.success(request, "Visibility rule deleted.")
    return redirect(f"/applicants/builder/fields/{field_id}/edit/")


@_admin_required
def logic_create(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    if request.method == "POST":
        source_field_id = request.POST.get("source_field")
        target_raw = request.POST.get("target_field", "")
        operator = request.POST.get("operator", "equals")
        value = request.POST.get("value", "")
        action_type = request.POST.get("action_type", "show")

        source_field = get_object_or_404(FormField, pk=source_field_id)

        if target_raw.startswith("field:"):
            target_field_id = int(target_raw.split(":")[1])
            target_field = get_object_or_404(FormField, pk=target_field_id)
        elif target_raw.startswith("section:"):
            section_id = int(target_raw.split(":")[1])
            first_field = FormField.objects.filter(section_id=section_id).first()
            if not first_field:
                messages.error(request, "Section has no fields to target.")
                return redirect(f"/applicants/builder/forms/{form_id}/edit/")
            target_field = first_field
        else:
            messages.error(request, "Invalid target.")
            return redirect(f"/applicants/builder/forms/{form_id}/edit/")

        op_map = {
            "equals": "eq", "not_equals": "neq", "contains": "contains",
            "not_empty": "not_empty", "empty": "is_empty",
            "greater_than": "gt", "less_than": "lt",
        }

        VisibilityRule.objects.create(
            field=target_field,
            target_field=source_field,
            operator=op_map.get(operator, operator),
            value=value,
            logic_operator="AND",
            sort_order=0,
            action=request.POST.get("action_type", "show"),
        )
        messages.success(request, "Conditional rule added.")
    return redirect(f"/applicants/builder/forms/{form_id}/edit/")


@_admin_required
def logic_delete(request: HttpRequest, rule_id: int) -> HttpResponse:
    rule = get_object_or_404(VisibilityRule, pk=rule_id)
    form_id = rule.field.section.form_id
    if request.method == "POST":
        rule.delete()
        messages.success(request, "Rule deleted.")
    return redirect(f"/applicants/builder/forms/{form_id}/edit/")


# ─── Reordering (AJAX) ─────────────────────────────────────────────────


@_admin_required
def reorder_sections(request: HttpRequest, form_id: int) -> JsonResponse:
    if request.method == "POST":
        data = json.loads(request.body)
        for item in data.get("items", []):
            FormSection.objects.filter(pk=item["id"]).update(
                sort_order=item["order"]
            )
        return JsonResponse({"success": True})
    return JsonResponse({"error": "POST required"}, status=405)


@_admin_required
def reorder_fields(request: HttpRequest, section_id: int) -> JsonResponse:
    if request.method == "POST":
        data = json.loads(request.body)
        for item in data.get("items", []):
            FormField.objects.filter(pk=item["id"]).update(
                sort_order=item["order"]
            )
        return JsonResponse({"success": True})
    return JsonResponse({"error": "POST required"}, status=405)


# ─── Preview ───────────────────────────────────────────────────────────


def _build_form_preview_sections(form_def) -> list:
    """Build the per-field context structure used by the applicant-form renderer."""
    context_data = []
    sections = form_def.sections.filter(is_active=True).order_by("sort_order")
    for section in sections:
        fields = (
            FormField.objects.filter(section=section, is_active=True)
            .order_by("sort_order")
            .prefetch_related("choices", "validations")
        )
        field_data = []
        for field in fields:
            field_data.append(
                {
                    "field": field,
                    "is_required": field.is_required,
                    "choices": FieldChoice.objects.filter(
                        field=field, is_active=True
                    ).order_by("sort_order"),
                    "validations": ValidationRule.objects.filter(
                        field=field, is_active=True
                    ).order_by("sort_order"),
                    "visibility": VisibilityRule.objects.filter(
                        field=field, is_active=True
                    ).order_by("sort_order"),
                    "value": field.default_value,
                }
            )
        context_data.append(
            {
                "section": section,
                "fields": field_data,
                "response": None,
                "repeat_index": 0,
            }
        )
    return context_data


@_admin_required
def form_preview(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    context_data = _build_form_preview_sections(form_def)
    return render(
        request,
        "Applicants/builder/preview.html",
        {"form_def": form_def, "sections": context_data},
    )


# ─── Workflow ──────────────────────────────────────────────────────────


@_admin_required
def workflow_list(request: HttpRequest) -> HttpResponse:
    workflows = WorkflowDefinition.objects.all().order_by("code")
    return render(
        request,
        "Applicants/builder/workflow_list.html",
        {"workflows": workflows},
    )


@_admin_required
def workflow_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        if not code or not name:
            messages.error(request, "Code and Name are required.")
            return redirect("builder_workflow_create")
        wf = WorkflowDefinition.objects.create(
            code=code,
            name=name,
            description=request.POST.get("description", ""),
            is_default=request.POST.get("is_default") == "on",
        )
        messages.success(request, f"Workflow '{name}' created.")
        return redirect(f"/applicants/builder/workflows/{wf.pk}/edit/")
    return render(request, "Applicants/builder/workflow_create.html")


@_admin_required
def workflow_edit(request: HttpRequest, workflow_id: int) -> HttpResponse:
    wf = get_object_or_404(WorkflowDefinition, pk=workflow_id)
    if request.method == "POST":
        wf.name = request.POST.get("name", wf.name)
        wf.description = request.POST.get("description", "")
        wf.code = request.POST.get("code", wf.code)
        wf.is_active = request.POST.get("is_active") == "on"
        wf.is_default = request.POST.get("is_default") == "on"
        wf.applicant_type = request.POST.get("applicant_type", "") or None
        wf.save()
        messages.success(request, "Workflow updated.")
        return redirect("builder_workflow_edit", workflow_id=workflow_id)

    steps = (
        DynamicWorkflowStep.objects.filter(workflow=wf, is_active=True)
        .order_by("sort_order")
        .prefetch_related("conditions")
    )
    forms = FormDefinition.objects.filter(is_active=True).order_by("sort_order")
    return render(
        request,
        "Applicants/builder/workflow_edit.html",
        {
            "wf": wf,
            "steps": steps,
            "forms": forms,
            "step_types": DynamicWorkflowStep._meta.get_field(
                "step_type"
            ).choices,
            "condition_operators": StepCondition._meta.get_field(
                "operator"
            ).choices,
        },
    )


@_admin_required
def workflow_delete(request: HttpRequest, workflow_id: int) -> HttpResponse:
    wf = get_object_or_404(WorkflowDefinition, pk=workflow_id)
    if request.method == "POST":
        name = wf.name
        wf.delete()
        messages.success(request, f"Workflow '{name}' deleted.")
        return redirect("builder_workflow_list")
    return render(
        request,
        "Applicants/builder/workflow_delete.html",
        {"wf": wf},
    )


# ─── Workflow Steps ────────────────────────────────────────────────────


@_admin_required
def workflow_step_add(request: HttpRequest, workflow_id: int) -> HttpResponse:
    wf = get_object_or_404(WorkflowDefinition, pk=workflow_id)
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        step_type = request.POST.get("step_type", "form")
        form_id = request.POST.get("form_id") or None
        last = (
            DynamicWorkflowStep.objects.filter(workflow=wf)
            .order_by("-sort_order")
            .first()
        )
        sort_order = int(request.POST.get("sort_order", 0)) or (
            last.sort_order + 1 if last else 1
        )
        DynamicWorkflowStep.objects.create(
            workflow=wf,
            code=code,
            name=name,
            description=request.POST.get("description", ""),
            step_type=step_type,
            form_id=form_id,
            sort_order=sort_order,
            is_required=request.POST.get("is_required") == "on",
            is_skippable=request.POST.get("is_skippable") == "on",
            group=request.POST.get("group", ""),
        )
        messages.success(request, f"Step '{name}' added.")
    return redirect("builder_workflow_edit", workflow_id=workflow_id)


@_admin_required
def workflow_step_edit(request: HttpRequest, step_id: int) -> HttpResponse:
    step = get_object_or_404(DynamicWorkflowStep, pk=step_id)
    if request.method == "POST":
        step.code = request.POST.get("code", step.code)
        step.name = request.POST.get("name", step.name)
        step.description = request.POST.get("description", "")
        step.step_type = request.POST.get("step_type", step.step_type)
        step.form_id = request.POST.get("form_id") or None
        step.sort_order = int(request.POST.get("sort_order", step.sort_order))
        step.is_required = request.POST.get("is_required") == "on"
        step.is_skippable = request.POST.get("is_skippable") == "on"
        step.group = request.POST.get("group", "")
        step.is_active = request.POST.get("is_active") == "on"
        step.save()
        messages.success(request, "Step updated.")
    return redirect("builder_workflow_edit", workflow_id=step.workflow_id)


@_admin_required
def workflow_step_delete(
    request: HttpRequest, step_id: int
) -> HttpResponse:
    step = get_object_or_404(DynamicWorkflowStep, pk=step_id)
    wf_id = step.workflow_id
    if request.method == "POST":
        step.delete()
        messages.success(request, "Step deleted.")
    return redirect("builder_workflow_edit", workflow_id=wf_id)


# ─── Workflow Step Conditions ──────────────────────────────────────────


@_admin_required
def workflow_step_condition_add(
    request: HttpRequest, step_id: int
) -> HttpResponse:
    step = get_object_or_404(DynamicWorkflowStep, pk=step_id)
    if request.method == "POST":
        target = request.POST.get("target_field", "")
        operator = request.POST.get("operator", "eq")
        value = request.POST.get("value", "")
        if target:
            StepCondition.objects.create(
                step=step,
                target_field=target,
                operator=operator,
                value=value,
                logic_operator=request.POST.get("logic_operator", "AND"),
            )
            messages.success(request, "Condition added.")
    return redirect("builder_workflow_edit", workflow_id=step.workflow_id)


@_admin_required
def workflow_step_condition_delete(
    request: HttpRequest, condition_id: int
) -> HttpResponse:
    condition = get_object_or_404(StepCondition, pk=condition_id)
    wf_id = condition.step.workflow_id
    if request.method == "POST":
        condition.delete()
        messages.success(request, "Condition deleted.")
    return redirect("builder_workflow_edit", workflow_id=wf_id)


# ─── Form Assignments ──────────────────────────────────────────────────


@_admin_required
def assignments(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    assignments_qs = FormAssignment.objects.filter(form=form_def).order_by(
        "sort_order"
    )
    if request.method == "POST":
        FormAssignment.objects.create(
            form=form_def,
            university_id=request.POST.get("university") or None,
            degree_level_id=request.POST.get("degree_level") or None,
            applicant_type=request.POST.get("applicant_type", "") or None,
            program_id=request.POST.get("program") or None,
            is_required=request.POST.get("is_required") == "on",
            sort_order=int(request.POST.get("sort_order", 0)),
        )
        messages.success(request, "Assignment added.")
        return redirect("builder_assignments", form_id=form_id)

    universities = University.objects.filter(status="ACTIVE")
    degrees = Degree.objects.all()
    programs = AcademicProgram.objects.all()
    applicant_types = [
        ("first_year", "First-Year"),
        ("transfer", "Transfer"),
        ("international_first_year", "International First-Year"),
        ("international_transfer", "International Transfer"),
        ("masters", "Master's"),
        ("phd", "PhD"),
        ("graduate_certificate", "Graduate Certificate"),
    ]
    return render(
        request,
        "Applicants/builder/assignments.html",
        {
            "form_def": form_def,
            "assignments": assignments_qs,
            "universities": universities,
            "degrees": degrees,
            "programs": programs,
            "applicant_types": applicant_types,
        },
    )


@_admin_required
def assignment_delete(
    request: HttpRequest, assignment_id: int
) -> HttpResponse:
    assignment = get_object_or_404(FormAssignment, pk=assignment_id)
    form_id = assignment.form_id
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Assignment deleted.")
    return redirect(f"/applicants/builder/forms/{form_id}/assignments/")


@_admin_required
def section_assignments(request: HttpRequest, form_id: int) -> HttpResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    sections = form_def.sections.filter(is_active=True).order_by("sort_order")
    assignments_qs = SectionAssignment.objects.filter(
        section__form=form_def
    ).select_related("section").order_by("section__sort_order", "sort_order")

    if request.method == "POST":
        section_id = request.POST.get("section")
        section = get_object_or_404(FormSection, pk=section_id, form=form_def)
        SectionAssignment.objects.create(
            section=section,
            university_id=request.POST.get("university") or None,
            degree_level_id=request.POST.get("degree_level") or None,
            applicant_type=request.POST.get("applicant_type", "") or None,
            program_id=request.POST.get("program") or None,
            is_required=request.POST.get("is_required") == "on",
            sort_order=int(request.POST.get("sort_order", 0)),
        )
        messages.success(request, f"Assignment added for '{section.title}'.")
        return redirect("builder_section_assignments", form_id=form_id)

    universities = University.objects.filter(status="ACTIVE")
    degrees = Degree.objects.all()
    programs = AcademicProgram.objects.all()
    applicant_types = [
        ("first_year", "First-Year"),
        ("transfer", "Transfer"),
        ("international_first_year", "International First-Year"),
        ("international_transfer", "International Transfer"),
        ("masters", "Master's"),
        ("phd", "PhD"),
        ("graduate_certificate", "Graduate Certificate"),
    ]
    return render(
        request,
        "Applicants/builder/section_assignments.html",
        {
            "form_def": form_def,
            "sections": sections,
            "assignments": assignments_qs,
            "universities": universities,
            "degrees": degrees,
            "programs": programs,
            "applicant_types": applicant_types,
        },
    )


@_admin_required
def section_assignment_delete(
    request: HttpRequest, assignment_id: int
) -> HttpResponse:
    assignment = get_object_or_404(SectionAssignment, pk=assignment_id)
    form_id = assignment.section.form_id
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Section assignment deleted.")
    return redirect(f"/applicants/builder/forms/{form_id}/section-assignments/")


# ─── API Helpers ───────────────────────────────────────────────────────


@_admin_required
def api_form_fields(request: HttpRequest, form_id: int) -> JsonResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    sections = form_def.sections.filter(is_active=True).order_by("sort_order")
    data = []
    for section in sections:
        fields = FormField.objects.filter(
            section=section, is_active=True
        ).order_by("sort_order")
        data.append(
            {
                "section": {
                    "id": section.pk,
                    "code": section.code,
                    "title": section.title,
                },
                "fields": [
                    {
                        "id": f.pk,
                        "code": f.code,
                        "label": f.label,
                        "field_type": f.field_type,
                    }
                    for f in fields
                ],
            }
        )
    return JsonResponse(data, safe=False)


@_admin_required
def api_form_preview_data(
    request: HttpRequest, form_id: int
) -> JsonResponse:
    form_def = get_object_or_404(FormDefinition, pk=form_id)
    data = {
        "id": form_def.pk,
        "code": form_def.code,
        "name": form_def.name,
        "sections": [],
    }
    for section in form_def.sections.filter(is_active=True).order_by("sort_order"):
        section_data = {
            "id": section.pk,
            "code": section.code,
            "title": section.title,
            "is_repeatable": section.is_repeatable,
            "render_as": section.render_as,
            "fields": [],
        }
        for field in FormField.objects.filter(
            section=section, is_active=True
        ).order_by("sort_order"):
            choices = [
                {"value": c.value, "label": c.label}
                for c in FieldChoice.objects.filter(
                    field=field, is_active=True
                ).order_by("sort_order")
            ]
            validations = [
                {
                    "type": v.validation_type,
                    "value": v.value,
                    "msg": v.error_message,
                }
                for v in ValidationRule.objects.filter(
                    field=field, is_active=True
                ).order_by("sort_order")
            ]
            section_data["fields"].append(
                {
                    "id": field.pk,
                    "code": field.code,
                    "label": field.label,
                    "field_type": field.field_type,
                    "placeholder": field.placeholder,
                    "layout_width": field.layout_width,
                    "is_required": field.is_required,
                    "choices": choices,
                    "validations": validations,
                }
            )
        data["sections"].append(section_data)
    return JsonResponse(data)


# ═══════════════════════════════════════════════════════════════════════
# Admission Cycle CRUD
# ═══════════════════════════════════════════════════════════════════════

@_admin_required
def cycle_list(request: HttpRequest) -> HttpResponse:
    cycles = AdmissionCycle.objects.all().order_by("-application_deadline")
    return render(request, "Applicants/builder/cycle_list.html", {"cycles": cycles})


@_admin_required
def cycle_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        term = request.POST.get("name", "")
        year = request.POST.get("year", "")
        name = f"{term} {year}" if term and year else term
        code = request.POST.get("code")
        academic_year = f"{year}-{int(year)+1}" if year else ""
        deadline_type = request.POST.get("deadline_type")
        application_start = request.POST.get("application_start")
        application_deadline = request.POST.get("application_deadline")
        materials_deadline = request.POST.get("materials_deadline") or None
        decision_release = request.POST.get("decision_release") or None
        is_active = request.POST.get("is_active") == "on"
        is_open = request.POST.get("is_open") == "on"

        try:
            from django.utils.dateparse import parse_date
            AdmissionCycle.objects.create(
                name=name, code=code, academic_year=academic_year,
                term=term, deadline_type=deadline_type,
                application_start=parse_date(application_start),
                application_deadline=parse_date(application_deadline),
                materials_deadline=parse_date(materials_deadline) if materials_deadline else None,
                decision_release=parse_date(decision_release) if decision_release else None,
                is_active=is_active, is_open=is_open,
            )
            messages.success(request, "Admission cycle created.")
            return redirect("builder_cycle_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, "Applicants/builder/cycle_form.html", {
        "cycle": None,
        "deadline_types": AdmissionCycle.DEADLINE_TYPE_CHOICES,
    })


@_admin_required
def cycle_edit(request: HttpRequest, cycle_id: int) -> HttpResponse:
    cycle = get_object_or_404(AdmissionCycle, pk=cycle_id)
    if request.method == "POST":
        try:
            from django.utils.dateparse import parse_date
            term = request.POST.get("name", "")
            year = request.POST.get("year", "")
            cycle.name = f"{term} {year}" if term and year else term
            cycle.code = request.POST.get("code")
            cycle.academic_year = f"{year}-{int(year)+1}" if year else ""
            cycle.term = term
            cycle.deadline_type = request.POST.get("deadline_type")
            cycle.application_start = parse_date(request.POST.get("application_start"))
            cycle.application_deadline = parse_date(request.POST.get("application_deadline"))
            cycle.materials_deadline = parse_date(request.POST.get("materials_deadline")) if request.POST.get("materials_deadline") else None
            cycle.decision_release = parse_date(request.POST.get("decision_release")) if request.POST.get("decision_release") else None
            cycle.is_active = request.POST.get("is_active") == "on"
            cycle.is_open = request.POST.get("is_open") == "on"
            cycle.save()
            messages.success(request, "Admission cycle updated.")
            return redirect("builder_cycle_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, "Applicants/builder/cycle_form.html", {
        "cycle": cycle,
        "cycle_term": cycle.term or cycle.name.rsplit(" ", 1)[0] if cycle.name else "",
        "cycle_year": cycle.name.rsplit(" ", 1)[-1] if cycle.name and " " in cycle.name else "",
        "deadline_types": AdmissionCycle.DEADLINE_TYPE_CHOICES,
    })


@_admin_required
def cycle_delete(request: HttpRequest, cycle_id: int) -> HttpResponse:
    cycle = get_object_or_404(AdmissionCycle, pk=cycle_id)
    if request.method == "POST":
        try:
            name = cycle.name
            cycle.delete()
            messages.success(request, f'Cycle "{name}" deleted.')
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect("builder_cycle_list")
    return render(request, "Applicants/builder/cycle_delete.html", {"cycle": cycle})


# ═══════════════════════════════════════════════════════════════
# Application Fees CRUD
# ═══════════════════════════════════════════════════════════════

@_admin_required
def fee_list(request: HttpRequest) -> HttpResponse:
    fees = ApplicationFee.objects.select_related("university", "degree_level").order_by("university__university_name", "degree_level__degree_name")
    return render(request, "Applicants/builder/fee_list.html", {"fees": fees})


@_admin_required
def fee_create(request: HttpRequest) -> HttpResponse:
    universities = University.objects.all().order_by("university_name")
    degrees = Degree.objects.all().order_by("degree_name")
    if request.method == "POST":
        try:
            university_id = request.POST.get("university") or None
            degree_id = request.POST.get("degree_level") or None
            ApplicationFee.objects.create(
                university=University.objects.get(pk=university_id) if university_id else None,
                degree_level=Degree.objects.get(pk=degree_id) if degree_id else None,
                amount=request.POST.get("amount", "0"),
                currency=request.POST.get("currency", "USD"),
                waiver_available=request.POST.get("waiver_available") == "on",
            )
            messages.success(request, "Application fee created.")
            return redirect("builder_fee_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "Applicants/builder/fee_form.html", {
        "fee": None, "universities": universities, "degrees": degrees,
    })


@_admin_required
def fee_edit(request: HttpRequest, fee_id: int) -> HttpResponse:
    fee = get_object_or_404(ApplicationFee, pk=fee_id)
    universities = University.objects.all().order_by("university_name")
    degrees = Degree.objects.all().order_by("degree_name")
    if request.method == "POST":
        try:
            university_id = request.POST.get("university") or None
            degree_id = request.POST.get("degree_level") or None
            fee.university = University.objects.get(pk=university_id) if university_id else None
            fee.degree_level = Degree.objects.get(pk=degree_id) if degree_id else None
            fee.amount = request.POST.get("amount", "0")
            fee.currency = request.POST.get("currency", "USD")
            fee.waiver_available = request.POST.get("waiver_available") == "on"
            fee.save()
            messages.success(request, "Application fee updated.")
            return redirect("builder_fee_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "Applicants/builder/fee_form.html", {
        "fee": fee, "universities": universities, "degrees": degrees,
    })


@_admin_required
def fee_delete(request: HttpRequest, fee_id: int) -> HttpResponse:
    fee = get_object_or_404(ApplicationFee, pk=fee_id)
    if request.method == "POST":
        try:
            fee.delete()
            messages.success(request, "Application fee deleted.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect("builder_fee_list")
    return render(request, "Applicants/builder/fee_delete.html", {"fee": fee})


# ═══════════════════════════════════════════════════════════════
# Applicant Type Requirements CRUD
# ═══════════════════════════════════════════════════════════════

@_admin_required
def req_type_list(request: HttpRequest) -> HttpResponse:
    reqs = ApplicantTypeRequirement.objects.select_related("degree_level").all().order_by("applicant_type")
    return render(request, "Applicants/builder/req_type_list.html", {"reqs": reqs})


@_admin_required
def req_type_create(request: HttpRequest) -> HttpResponse:
    degrees = Degree.objects.all().order_by("degree_name")
    if request.method == "POST":
        try:
            degree_id = request.POST.get("degree_level") or None
            ApplicantTypeRequirement.objects.create(
                applicant_type=request.POST.get("applicant_type", "first_year"),
                degree_level=Degree.objects.get(pk=degree_id) if degree_id else None,
                requires_transcript=request.POST.get("requires_transcript") == "on",
                requires_high_school_courses=request.POST.get("requires_high_school_courses") == "on",
                requires_college_transcript=request.POST.get("requires_college_transcript") == "on",
                requires_essay=request.POST.get("requires_essay") == "on",
                requires_activities=request.POST.get("requires_activities") == "on",
                requires_honors=request.POST.get("requires_honors") == "on",
                requires_test_scores=request.POST.get("requires_test_scores") == "on",
                test_optional=request.POST.get("test_optional") == "on",
                requires_resume=request.POST.get("requires_resume") == "on",
                min_transfer_credits=request.POST.get("min_transfer_credits") or None,
                is_active=request.POST.get("is_active") == "on",
            )
            messages.success(request, "Applicant type requirement created.")
            return redirect("builder_req_type_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "Applicants/builder/req_type_form.html", {
        "req": None, "degrees": degrees,
        "applicant_types": ApplicantTypeRequirement.APPLICANT_TYPE_CHOICES,
    })


@_admin_required
def req_type_edit(request: HttpRequest, req_id: int) -> HttpResponse:
    req = get_object_or_404(ApplicantTypeRequirement, pk=req_id)
    degrees = Degree.objects.all().order_by("degree_name")
    if request.method == "POST":
        try:
            degree_id = request.POST.get("degree_level") or None
            req.applicant_type = request.POST.get("applicant_type", "first_year")
            req.degree_level = Degree.objects.get(pk=degree_id) if degree_id else None
            req.requires_transcript = request.POST.get("requires_transcript") == "on"
            req.requires_high_school_courses = request.POST.get("requires_high_school_courses") == "on"
            req.requires_college_transcript = request.POST.get("requires_college_transcript") == "on"
            req.requires_essay = request.POST.get("requires_essay") == "on"
            req.requires_activities = request.POST.get("requires_activities") == "on"
            req.requires_honors = request.POST.get("requires_honors") == "on"
            req.requires_test_scores = request.POST.get("requires_test_scores") == "on"
            req.test_optional = request.POST.get("test_optional") == "on"
            req.requires_resume = request.POST.get("requires_resume") == "on"
            val = request.POST.get("min_transfer_credits")
            req.min_transfer_credits = int(val) if val else None
            req.is_active = request.POST.get("is_active") == "on"
            req.save()
            messages.success(request, "Applicant type requirement updated.")
            return redirect("builder_req_type_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "Applicants/builder/req_type_form.html", {
        "req": req, "degrees": degrees,
        "applicant_types": ApplicantTypeRequirement.APPLICANT_TYPE_CHOICES,
    })


@_admin_required
def req_type_delete(request: HttpRequest, req_id: int) -> HttpResponse:
    req = get_object_or_404(ApplicantTypeRequirement, pk=req_id)
    if request.method == "POST":
        try:
            req.delete()
            messages.success(request, "Applicant type requirement deleted.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect("builder_req_type_list")
    return render(request, "Applicants/builder/req_type_delete.html", {"req": req})


# ═══════════════════════════════════════════════════════════════
# Document Requirements CRUD
# ═══════════════════════════════════════════════════════════════

@_admin_required
def doc_req_list(request: HttpRequest) -> HttpResponse:
    doc_reqs = DocumentRequirement.objects.select_related("university", "degree_level", "program").all().order_by("university__university_name", "degree_level__degree_name", "sort_order")
    return render(request, "Applicants/builder/doc_req_list.html", {"doc_reqs": doc_reqs})


def _doc_req_presets():
    return [
        {"code": "transcript_hs", "name": "High School Transcript", "category": "academic", "extensions": ".pdf", "max_files": 1},
        {"code": "hs_grades", "name": "High School Grade Sheet", "category": "academic", "extensions": ".pdf", "max_files": 1},
        {"code": "transcript_college", "name": "College Transcript", "category": "academic", "extensions": ".pdf", "max_files": 1},
        {"code": "transcript_grad", "name": "Graduate Transcript", "category": "academic", "extensions": ".pdf", "max_files": 1},
        {"code": "hs_courses", "name": "High School Course List", "category": "academic", "extensions": ".pdf,.csv", "max_files": 1},
        {"code": "diploma", "name": "High School Diploma / GED", "category": "academic", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "essay_personal", "name": "Personal Essay", "category": "essay", "extensions": ".pdf,.doc,.docx", "max_files": 1},
        {"code": "essay_supplemental", "name": "Supplemental Essay", "category": "essay", "extensions": ".pdf,.doc,.docx", "max_files": 3},
        {"code": "essay_short_answer", "name": "Short Answer Responses", "category": "essay", "extensions": ".pdf,.doc,.docx", "max_files": 1},
        {"code": "test_sat", "name": "SAT Score Report", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "test_act", "name": "ACT Score Report", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "test_gre", "name": "GRE Score Report", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "test_gmat", "name": "GMAT Score Report", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "test_toefl", "name": "TOEFL Score Report", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "test_ielts", "name": "IELTS Score Report", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "test_duolingo", "name": "Duolingo English Test", "category": "test_score", "extensions": ".pdf", "max_files": 1},
        {"code": "resume", "name": "Resume / CV", "category": "other", "extensions": ".pdf,.doc,.docx", "max_files": 1},
        {"code": "portfolio", "name": "Portfolio", "category": "portfolio", "extensions": ".pdf,.jpg,.png,.zip", "max_files": 5},
        {"code": "writing_sample", "name": "Writing Sample", "category": "essay", "extensions": ".pdf,.doc,.docx", "max_files": 2},
        {"code": "financial_statement", "name": "Financial Statement", "category": "financial", "extensions": ".pdf", "max_files": 1},
        {"code": "affidavit_support", "name": "Affidavit of Financial Support", "category": "financial", "extensions": ".pdf", "max_files": 1},
        {"code": "bank_statement", "name": "Bank Statement", "category": "financial", "extensions": ".pdf", "max_files": 3},
        {"code": "tax_return", "name": "Tax Return", "category": "financial", "extensions": ".pdf", "max_files": 2},
        {"code": "passport", "name": "Passport Copy", "category": "identification", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "national_id", "name": "National ID", "category": "identification", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "birth_certificate", "name": "Birth Certificate", "category": "identification", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "visa_i20", "name": "I-20 Form", "category": "legal", "extensions": ".pdf", "max_files": 1},
        {"code": "visa_passport", "name": "Passport Visa Page", "category": "legal", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "i94", "name": "I-94 Arrival Record", "category": "legal", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "green_card", "name": "Green Card / Permanent Residency", "category": "legal", "extensions": ".pdf,.jpg,.png", "max_files": 1},
        {"code": "dad", "name": "Deferred Action for Dreamers (DACA)", "category": "legal", "extensions": ".pdf", "max_files": 1},
        {"code": "military_dd214", "name": "DD-214 Military Discharge", "category": "military", "extensions": ".pdf", "max_files": 1},
        {"code": "military_orders", "name": "Military Orders / PCS", "category": "military", "extensions": ".pdf", "max_files": 1},
        {"code": "va_benefits", "name": "VA Benefits Certificate", "category": "military", "extensions": ".pdf", "max_files": 1},
        {"code": "health_immunization", "name": "Immunization Records", "category": "other", "extensions": ".pdf,.jpg,.png", "max_files": 3},
        {"code": "health_physical", "name": "Physical Exam Record", "category": "other", "extensions": ".pdf,.jpg,.png", "max_files": 1},
    ]


@_admin_required
def doc_req_create(request: HttpRequest) -> HttpResponse:
    universities = University.objects.all().order_by("university_name")
    degrees = Degree.objects.all().order_by("degree_name")
    programs = AcademicProgram.objects.filter(status="ACTIVE").order_by("program_name")
    if request.method == "POST":
        try:
            university_id = request.POST.get("university") or None
            degree_id = request.POST.get("degree_level") or None
            program_id = request.POST.get("program") or None
            code = request.POST.get("code", "").strip()
            name = request.POST.get("name", "").strip()
            if code == "__custom":
                code = request.POST.get("custom_code", "").strip()
                name = request.POST.get("custom_name", "").strip()
            DocumentRequirement.objects.create(
                code=code,
                name=name,
                description=request.POST.get("description", ""),
                category=request.POST.get("category", "academic"),
                university=University.objects.get(pk=university_id) if university_id else None,
                degree_level=Degree.objects.get(pk=degree_id) if degree_id else None,
                applicant_type=request.POST.get("applicant_type") or None,
                program=AcademicProgram.objects.get(pk=program_id) if program_id else None,
                is_required=request.POST.get("is_required") == "on",
                max_file_size_mb=int(request.POST.get("max_file_size_mb", "10")),
                allowed_extensions=request.POST.get("allowed_extensions", ".pdf,.doc,.docx,.jpg,.png"),
                max_files=int(request.POST.get("max_files", "1")),
                sort_order=int(request.POST.get("sort_order", "0")),
            )
            messages.success(request, "Document requirement created.")
            return redirect("builder_doc_req_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "Applicants/builder/doc_req_form.html", {
        "doc_req": None, "universities": universities, "degrees": degrees, "programs": programs,
        "categories": DOCUMENT_CATEGORY_CHOICES,
        "applicant_types": Application.APPLICANT_TYPE_CHOICES,
        "presets": _doc_req_presets(),
        "preset_codes": [p["code"] for p in _doc_req_presets()],
    })


@_admin_required
def doc_req_edit(request: HttpRequest, doc_req_id: int) -> HttpResponse:
    doc_req = get_object_or_404(DocumentRequirement, pk=doc_req_id)
    universities = University.objects.all().order_by("university_name")
    degrees = Degree.objects.all().order_by("degree_name")
    programs = AcademicProgram.objects.filter(status="ACTIVE").order_by("program_name")
    if request.method == "POST":
        try:
            university_id = request.POST.get("university") or None
            degree_id = request.POST.get("degree_level") or None
            program_id = request.POST.get("program") or None
            code = request.POST.get("code", "").strip()
            name = request.POST.get("name", "").strip()
            if code == "__custom":
                code = request.POST.get("custom_code", "").strip()
                name = request.POST.get("custom_name", "").strip()
            doc_req.code = code
            doc_req.name = name
            doc_req.description = request.POST.get("description", "")
            doc_req.category = request.POST.get("category", "academic")
            doc_req.university = University.objects.get(pk=university_id) if university_id else None
            doc_req.degree_level = Degree.objects.get(pk=degree_id) if degree_id else None
            doc_req.applicant_type = request.POST.get("applicant_type") or None
            doc_req.program = AcademicProgram.objects.get(pk=program_id) if program_id else None
            doc_req.is_required = request.POST.get("is_required") == "on"
            doc_req.max_file_size_mb = int(request.POST.get("max_file_size_mb", "10"))
            doc_req.allowed_extensions = request.POST.get("allowed_extensions", ".pdf,.doc,.docx,.jpg,.png")
            doc_req.max_files = int(request.POST.get("max_files", "1"))
            doc_req.sort_order = int(request.POST.get("sort_order", "0"))
            doc_req.save()
            messages.success(request, "Document requirement updated.")
            return redirect("builder_doc_req_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "Applicants/builder/doc_req_form.html", {
        "doc_req": doc_req, "universities": universities, "degrees": degrees, "programs": programs,
        "categories": DOCUMENT_CATEGORY_CHOICES,
        "applicant_types": Application.APPLICANT_TYPE_CHOICES,
        "presets": _doc_req_presets(),
        "preset_codes": [p["code"] for p in _doc_req_presets()],
    })


@_admin_required
def doc_req_delete(request: HttpRequest, doc_req_id: int) -> HttpResponse:
    doc_req = get_object_or_404(DocumentRequirement, pk=doc_req_id)
    if request.method == "POST":
        try:
            doc_req.delete()
            messages.success(request, "Document requirement deleted.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect("builder_doc_req_list")
    return render(request, "Applicants/builder/doc_req_delete.html", {"doc_req": doc_req})



