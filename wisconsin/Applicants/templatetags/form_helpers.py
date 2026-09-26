import json
import re
from datetime import date
from typing import Any, Optional

from django import template
from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe
from ..models import FormSection


register = template.Library()


@register.filter(name='split')
def split_string(value, delimiter=','):
    """Split a string by delimiter and return a list of stripped items."""
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]


FIELD_LIVE_PATTERNS = {
    "text": {"regex": r"^[\w\s\-'\"\,\.\#\&\/\(\)\!\?\:\;]{1,500}$", "msg": "Enter valid value."},
    "email": {"regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", "msg": "Enter valid email."},
    "phone": {"regex": r"^\+?1?\d{7,15}$", "msg": "Enter valid phone."},
    "url": {"regex": r"^https?:\/\/[\w\-\.]+\.\w{2,}[\w\-\.~:\/?#\[\]@!$&'()*+,;=]*$", "msg": "Enter valid URL."},
    "password": {"regex": r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", "msg": "Enter valid password."},
    "ssn": {"regex": r"^\d{3}-\d{2}-\d{4}$", "msg": "Enter valid SSN."},
    "textarea": {"regex": r"^[\w\s\-'\"\,\.\#\&\/\(\)\!\?\:\;\n\r]{1,10000}$", "msg": "Enter valid value."},
    "country": {"regex": r"^[a-zA-Z\s\'-]{2,100}$", "msg": "Enter valid country."},
    "state": {"regex": r"^[a-zA-Z\s\'-]{2,100}$", "msg": "Enter valid state."},
    "city": {"regex": r"^[a-zA-Z\s\'-]{2,100}$", "msg": "Enter valid city."},
    "first_name": {"regex": r"^[a-zA-Z\s\'-]{3,50}$", "msg": "Enter valid name."},
    "last_name": {"regex": r"^[a-zA-Z\s\'-]{1,50}$", "msg": "Enter valid name."},
    "year": {"regex": r"^\d{4}(-\d{2})?$", "msg": "Enter a valid year or year-month."},
}

_NAME_CODES = {"first_name", "firstname", "given_name"}
_LAST_CODES = {"last_name", "lastname", "family_name"}

def _detect_name_pattern(field_code: str, field_label: str):
    code_lower = field_code.lower().replace(" ", "_")
    label_lower = field_label.lower().replace(" ", "_")
    if any(c in code_lower or c in label_lower for c in _NAME_CODES):
        if any(c in code_lower or c in label_lower for c in ("last", "family")):
            return "last_name"
        return "first_name"
    if any(c in code_lower or c in label_lower for c in _LAST_CODES):
        return "last_name"
    return None

# ─── Filters ───────────────────────────────────────────────────────────


@register.filter
def field_type(field) -> str:
    widget_cls = field.field.widget.__class__.__name__.lower()
    if "checkboxinput" in widget_cls or "checkbox" in widget_cls:
        return "checkbox"
    if "textarea" in widget_cls:
        return "textarea"
    if "select" in widget_cls:
        return "select"
    return "text"


@register.filter
def lookup(d: Optional[dict], key: str) -> Any:
    return d.get(key, "") if d else ""


@register.filter
def section_label(code: str) -> str:
    section = FormSection.objects.filter(code=code, is_active=True).first()
    if section:
        return section.title
    return code.replace("_", " ").title()


@register.filter
def friendly(value) -> str:
    """Humanize a snake_case field/code name, e.g. 'material_upload' -> 'Material Upload'."""
    return str(value).replace("_", " ").title()


# ─── Render Tags ───────────────────────────────────────────────────────


@register.simple_tag(takes_context=True)
def render_dynamic_field(context, field_data: dict, _triggers: dict = None) -> SafeString:
    field = field_data["field"]
    choices = field_data["choices"]
    value = field_data.get("value", "")
    errors = field_data.get("errors", [])

    field_type = field.field_type
    field_code = field.code
    field_label = field.label
    field_placeholder = field.placeholder or ""
    field_help = field.help_text or ""
    required = field_data.get("is_required", False)
    validation_rules = {
        rule.validation_type: rule for rule in field_data.get("validations", [])
    }
    is_readonly = field.is_readonly
    layout = field.layout_width
    prefix = field.prefix_text or ""
    suffix = field.suffix_text or ""
    rows = field.rows or 4

    # ── Visual styling (from builder field properties) ──
    label_style = ""
    if getattr(field, "label_color", ""):
        label_style += f" color:{field.label_color};"
    if getattr(field, "font_size", ""):
        label_style += f" font-size:{field.font_size};"
    label_style_attr = f' style="{label_style.strip()}"' if label_style else ""

    input_style = ""
    if getattr(field, "input_color", ""):
        input_style += f" color:{field.input_color};"
    if getattr(field, "font_size", ""):
        input_style += f" font-size:{field.font_size};"
    if getattr(field, "input_background", ""):
        input_style += f" background-color:{field.input_background};"
    if getattr(field, "border_color", ""):
        input_style += f" border-color:{field.border_color};"
    if getattr(field, "input_height", ""):
        input_style += f" height:{field.input_height};"
    input_style_attr = f' style="{input_style.strip()}"' if input_style else ""

    html_parts = []

    visibility = field_data.get("visibility", [])
    is_conditional = bool(visibility)
    force_visible = field_data.get("force_visible", False)

    # ── Conditional trigger attributes (on wrapper for radio support) ──
    trigger_attrs = ""
    if _triggers and field_code in _triggers:
        info = _triggers[field_code]
        target_sel = ",".join(f"[data-field='{c}']" for c in info["targets"])
        trigger_attrs = (
            f' data-conditional-trigger="{field_code}"'
            f' data-conditional-target="{target_sel}"'
        )

    wrapper_class = "uw-form-group"
    if layout == "half":
        wrapper_class += " col-half"
    elif layout == "third":
        wrapper_class += " col-third"
    elif layout == "two_thirds":
        wrapper_class += " col-two-thirds"
    if is_conditional:
        wrapper_class += " uw-conditional-field"

    if is_conditional:
        cond_rules = json.dumps([
            {"f": v.target_field.code, "v": v.value, "op": v.operator, "l": v.logic_operator}
            for v in visibility
        ])
        cond_attr = f' data-conditional-rules=\'{cond_rules}\' data-conditional=""'
    else:
        cond_attr = ""
    style_attr = ' style="display:none"' if (is_conditional and not force_visible) else ""
    html_parts.append(
        f'<div class="{wrapper_class}" data-field="{field_code}"'
        f'{cond_attr}{trigger_attrs}{style_attr}>'
    )

    if field_type not in ("checkbox", "hidden", "heading"):
        label_attrs = f' for="id_{field_code}"'
        html_parts.append(f"<label{label_attrs}{label_style_attr}>{field_label}")
        if required:
            html_parts.append('<span class="text-c05">*</span>')
        html_parts.append("</label>")

    if prefix or suffix:
        html_parts.append('<div class="input-group">')
    if prefix:
        html_parts.append(f'<span class="input-group-prefix">{prefix}</span>')

    input_attrs = (
        f'id="id_{field_code}" name="{field_code}" '
        f'class="uw-input{" error" if errors else ""}"'
    )
    if input_style_attr:
        input_attrs += input_style_attr
    if required:
        input_attrs += " required"
    field_min = field_data.get("min_value_override") or (validation_rules["min_value"].value if "min_value" in validation_rules else None)
    if field_min:
        input_attrs += f' min="{field_min}"'
    elif field_type == "gpa":
        input_attrs += ' min="0"'
    elif field_type == "currency":
        input_attrs += ' min="0"'
    if "max_value" in validation_rules:
        input_attrs += f' max="{validation_rules["max_value"].value}"'
    elif field_type == "gpa":
        input_attrs += ' max="4.0"'
    if "max_length" in validation_rules:
        input_attrs += f' maxlength="{validation_rules["max_length"].value}"'
    name_key = _detect_name_pattern(field_code, field_label) if field_type == "text" else None
    if name_key:
        pattern = FIELD_LIVE_PATTERNS[name_key]
        input_attrs += f' data-live-regex="{pattern["regex"]}"'
        input_attrs += f' data-live-msg="{pattern["msg"]}"'
        if "msg_invalid" in pattern:
            input_attrs += f' data-live-msg-invalid="{pattern["msg_invalid"]}"'
    elif "regex" in validation_rules:
        rule = validation_rules["regex"]
        input_attrs += f' data-live-regex="{rule.value}"'
        if rule.error_message:
            input_attrs += f' data-live-msg="{rule.error_message}"'
    elif field_type in FIELD_LIVE_PATTERNS:
        pattern = FIELD_LIVE_PATTERNS[field_type]
        input_attrs += f' data-live-regex="{pattern["regex"]}"'
        input_attrs += f' data-live-msg="{pattern["msg"]}"'
    if "custom" in validation_rules:
        rule = validation_rules["custom"]
        if rule.value.startswith("match:"):
            input_attrs += f' data-match="{rule.value[6:]}"'
    if field_placeholder:
        input_attrs += f' placeholder="{field_placeholder}"'
    if is_readonly:
        input_attrs += " readonly"

    if field_help:
        html_parts.append(f'<span class="uw-help-text">{field_help}</span>')

    html_parts.append(_build_input_html(field_type, field_code, input_attrs, value, rows, choices, required, field_label, field_placeholder, errors))

    if prefix or suffix:
        if suffix:
            html_parts.append(f'<span class="input-group-suffix">{suffix}</span>')
        html_parts.append("</div>")

    for err in errors:
        html_parts.append(f'<span class="uw-field-error">{err}</span>')

    review_validation = field_data.get("review_validation")
    if review_validation:
        rv_ok = bool(review_validation.get("valid"))
        rv_msg = (review_validation.get("msg") or "").strip()
        rv_class = "prm-fr-badge prm-fr-badge--ok" if rv_ok else "prm-fr-badge prm-fr-badge--bad"
        rv_icon = "circle-check" if rv_ok else "alert-triangle"
        rv_label = "Passes validation" if rv_ok else "Fails validation"
        html_parts.append(
            f'<span class="{rv_class}"><i class="ti ti-{rv_icon}"></i> {rv_label}'
            f'<span class="prm-fr-badge__msg">{escape(rv_msg)}</span></span>'
        )

    html_parts.append("</div>")
    return mark_safe("".join(html_parts))


def _build_input_html(
    field_type: str,
    field_code: str,
    input_attrs: str,
    value: Any,
    rows: int,
    choices: list,
    required: bool,
    field_label: str,
    field_placeholder: str,
    errors: list,
) -> str:
    parts = []

    if field_type == "text":
        parts.append(f'<input type="text" {input_attrs} value="{value}" />')
    elif field_type == "email":
        parts.append(f'<input type="email" {input_attrs} value="{value}" />')
    elif field_type == "phone":
        parts.append(
            f'<span class="uw-phone-field" data-field="{field_code}">'
            f'<input type="tel" {input_attrs} value="{value}" />'
            f"</span>"
        )
    elif field_type == "url":
        parts.append(f'<input type="url" {input_attrs} value="{value}" />')
    elif field_type == "number":
        parts.append(f'<input type="number" {input_attrs} value="{value}" step="any" />')
    elif field_type == "year":
        year_v = month_v = ""
        if value:
            s = str(value)
            if "-" in s:
                try:
                    y, m = s.split("-")
                    year_v, month_v = y, m
                except: pass
            else:
                try:
                    year_v = str(int(float(s)))
                except: pass
        req = " required" if required else ""
        m_min = re.search(r'min="(\d+)"', input_attrs)
        m_max = re.search(r'max="(\d+)"', input_attrs)
        min_y = int(m_min.group(1)) if m_min else 1900
        max_y = int(m_max.group(1)) if m_max else 2099
        months = [
            ("", "Month"), ("01", "Jan"), ("02", "Feb"), ("03", "Mar"),
            ("04", "Apr"), ("05", "May"), ("06", "Jun"), ("07", "Jul"),
            ("08", "Aug"), ("09", "Sep"), ("10", "Oct"), ("11", "Nov"), ("12", "Dec")
        ]
        parts.append(f'<div class="uw-date-selects" data-year-field="{field_code}">')
        parts.append(f'<select class="uw-input uw-year-part"{req} data-part="month" aria-label="Month">')
        for v, l in months:
            parts.append(f'<option value="{v}"{" selected" if v == month_v else ""}>{l}</option>')
        parts.append('</select>')
        parts.append(f'<select class="uw-input uw-year-part"{req} data-part="year" aria-label="Year">')
        parts.append('<option value="">Year</option>')
        for y in range(max_y, min_y - 1, -1):
            ys = str(y)
            parts.append(f'<option value="{ys}"{" selected" if ys == year_v else ""}>{y}</option>')
        parts.append('</select>')
        parts.append(f'<input type="hidden" id="id_{field_code}" name="{field_code}" value="{value}" />')
        parts.append('</div>')
    elif field_type == "date":
        year_v = month_v = day_v = ""
        if value:
            try:
                y, m, d = str(value).split("-")
                year_v, month_v, day_v = y, m, d
            except: pass
        cur = date.today().year
        req = " required" if required else ""
        months = [
            ("", "Month"), ("01", "Jan"), ("02", "Feb"), ("03", "Mar"),
            ("04", "Apr"), ("05", "May"), ("06", "Jun"), ("07", "Jul"),
            ("08", "Aug"), ("09", "Sep"), ("10", "Oct"), ("11", "Nov"), ("12", "Dec")
        ]
        parts.append(f'<div class="uw-date-selects" data-date-field="{field_code}">')
        parts.append(f'<select class="uw-input uw-date-part"{req} data-part="month" aria-label="Month">')
        for v, l in months:
            parts.append(f'<option value="{v}"{" selected" if v == month_v else ""}>{l}</option>')
        parts.append('</select>')
        parts.append(f'<select class="uw-input uw-date-part"{req} data-part="day" aria-label="Day">')
        parts.append('<option value="">Day</option>')
        for d in range(1, 32):
            ds = f"{d:02d}"
            parts.append(f'<option value="{ds}"{" selected" if ds == day_v else ""}>{d}</option>')
        parts.append('</select>')
        parts.append(f'<select class="uw-input uw-date-part"{req} data-part="year" aria-label="Year">')
        parts.append('<option value="">Year</option>')
        for y in range(cur, cur - 101, -1):
            ys = str(y)
            parts.append(f'<option value="{ys}"{" selected" if ys == year_v else ""}>{y}</option>')
        parts.append('</select>')
        parts.append(f'<input type="hidden" id="id_{field_code}" name="{field_code}" value="{value}" {input_attrs} />')
        parts.append('</div>')
    elif field_type == "gpa":
        parts.append(f'<input type="number" {input_attrs} value="{value}" step="0.01" min="0" max="4.0" />')
    elif field_type == "currency":
        parts.append(f'<input type="number" {input_attrs} value="{value}" step="0.01" min="0" />')
    elif field_type == "password":
        parts.append(f'<input type="password" {input_attrs} />')
    elif field_type == "ssn":
        parts.append(f'<input type="password" {input_attrs} value="{value}" maxlength="11" />')
    elif field_type == "textarea":
        parts.append(f'<textarea {input_attrs} rows="{rows}">{value}</textarea>')
    elif field_type == "rich_text":
        parts.append(f'<textarea {input_attrs} rows="{rows}" class="uw-input rich-text-editor">{value}</textarea>')
    elif field_type == "select":
        parts.append(
            f'<select id="id_{field_code}" name="{field_code}" '
            f'class="uw-input uw-select{" error" if errors else ""}" '
            f'data-field="{field_code}" placeholder="{field_placeholder}"'
            f'{" required" if required else ""}>'
            f'<option value="">{"Select " + field_label}</option>'
        )
        for c in choices:
            sel = " selected" if str(c.value) == str(value) else ""
            parts.append(f'<option value="{c.value}"{sel}>{c.label}</option>')
        parts.append("</select>")
    elif field_type == "multi_select":
        selected_values = value if isinstance(value, list) else (value.split(",") if value else [])
        parts.append(
            f'<select id="id_{field_code}" name="{field_code}" '
            f'class="uw-input uw-select{" error" if errors else ""}" '
            f'data-field="{field_code}" multiple size="5"'
            f'{" required" if required else ""}>'
        )
        for c in choices:
            sel = " selected" if c.value in selected_values else ""
            parts.append(f'<option value="{c.value}"{sel}>{c.label}</option>')
        parts.append("</select>")
    elif field_type == "radio":
        parts.append(f'<div class="uw-radio-group" id="id_{field_code}">')
        for c in choices:
            checked = " checked" if str(c.value) == str(value) else ""
            parts.append(
                f'<label class="uw-radio-label">'
                f'<input type="radio" name="{field_code}" value="{c.value}"{checked}'
                f'{" required" if required else ""} /> '
                f'<span>{c.label}</span></label>'
            )
        parts.append("</div>")
    elif field_type == "checkbox":
        checked = ' checked' if str(value).lower() in ("true", "1", "on", "yes") else ""
        required_marker = ' <span class="text-c05">*</span>' if required else ""
        parts.append(
            f'<label class="uw-checkbox-label">'
            f'<input type="hidden" name="{field_code}" value="off" />'
            f'<input type="checkbox" name="{field_code}" value="on"{checked}'
            f'{" required" if required else ""} /> '
            f'<span>{field_label}{required_marker}</span></label>'
        )
    elif field_type in ("country", "state", "city"):
        parts.append(f'<input type="text" {input_attrs} value="{value}" />')
    elif field_type == "file":
        parts.append(f'<input type="file" {input_attrs} />')
        if value:
            parts.append(f'<div class="mt-2 fs-13 text-666">Current file: {value}</div>')
    elif field_type == "hidden":
        parts.append(f'<input type="hidden" name="{field_code}" value="{value}" />')
    elif field_type == "heading":
        if "\n" in field_label or len(field_label) > 100:
            parts.append(f'<p class="uw-field-desc">{field_label}</p>')
        else:
            parts.append(f'<h3 class="section-heading">{field_label}</h3>')

    return "".join(parts)


@register.simple_tag(takes_context=True)
def render_dynamic_section(context, section_data: dict) -> SafeString:
    section = section_data["section"]
    fields = section_data["fields"]
    repeat_index = section_data.get("repeat_index", 0)
    start_hidden = section.start_hidden and repeat_index == 0

    # ── Build visibility trigger → targets mapping ──────────────
    conditional_triggers = {}
    for fd in fields:
        vis_rules = fd.get("visibility", [])
        if not vis_rules:
            continue
        for rule in vis_rules:
            trigger_code = rule.target_field.code
            conditional_triggers.setdefault(trigger_code, {
                "targets": [],
            })
            conditional_triggers[trigger_code]["targets"].append(fd["field"].code)

    # Split heading vs other fields when start_hidden
    heading_fields = []
    other_fields = []
    if start_hidden:
        for fd in fields:
            if fd["field"].field_type == "heading":
                heading_fields.append(fd)
            else:
                other_fields.append(fd)

    html = []
    html.append(
        f'<div class="dynamic-section" data-section="{section.code}" data-repeat="{repeat_index}">'
    )

    if section.render_as == "card":
        html.append('<div class="uw-dash-card"><div class="uw-dash-card-body">')
    elif section.render_as == "fieldset":
        html.append('<fieldset class="uw-fieldset">')
        html.append(f'<legend class="uw-fieldset-legend">{section.title}</legend>')
    elif section.render_as == "accordion":
        html.append(f'<details class="uw-accordion-section">')
        html.append(f'<summary class="uw-accordion-title">{section.title}</summary>')
        html.append('<div class="uw-accordion-body">')

    if section.render_as == "card":
        html.append(f'<h3 class="card-section-title">{section.title}</h3>')
        if section.description:
            html.append(f'<p class="info-desc mb-4">{section.description}</p>')

    if section.is_repeatable:
        html.append(f'<input type="hidden" name="_repeat_index" value="{repeat_index}" />')

    if start_hidden:
        for fd in heading_fields:
            html.append(render_dynamic_field(context, fd, _triggers=conditional_triggers))
        if repeat_index == 0:
            html.append(
                f'<button type="button" class="uw-btn uw-btn-outline uw-btn-sm add-repeat mb-4" '
                f'data-section="{section.code}">+ Add {section.title}</button>'
            )
        html.append('<div class="dynamic-form-grid" style="display:none">')
        for fd in other_fields:
            html.append(render_dynamic_field(context, fd, _triggers=conditional_triggers))
        html.append("</div>")
    else:
        if section.is_repeatable and repeat_index == 0:
            html.append(
                f'<button type="button" class="uw-btn uw-btn-outline uw-btn-sm add-repeat mb-4" '
                f'data-section="{section.code}">+ Add {section.title}</button>'
            )
        html.append('<div class="dynamic-form-grid">')
        for fd in fields:
            html.append(render_dynamic_field(context, fd, _triggers=conditional_triggers))
        html.append("</div>")

    if section.render_as == "card":
        html.append("</div></div>")
    elif section.render_as == "fieldset":
        html.append("</fieldset>")
    elif section.render_as == "accordion":
        html.append("</div></details>")

    html.append("</div>")
    return mark_safe("".join(html))


@register.filter
def format_field_value(field_data: dict) -> SafeString:
    field_type = field_data.get("field_type", "text")
    value = field_data.get("value", "")
    if not value and value != 0:
        return mark_safe('<span class="text-ccc">\u2014</span>')
    if field_type == "checkbox":
        return "Yes" if str(value).lower() in ("true", "on", "yes", "1") else "No"
    if field_type == "file":
        return mark_safe(
            f'<a href="{value}" target="_blank">{field_data.get("file_name", value)}</a>'
        )
    if field_type == "currency":
        return f"${value}"
    if field_type == "url":
        return mark_safe(f'<a href="{value}" target="_blank">{value}</a>')
    if field_type == "multi_select":
        items = value if isinstance(value, list) else (json.loads(value) if value else [])
        return ", ".join(items) if items else "\u2014"
    if field_type == "year":
        if not value: return str(value)
        s = str(value)
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 2:
                months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                try:
                    return f"{months[int(parts[1])]} {parts[0]}"
                except: pass
        return str(int(float(s))) if s.replace(".","").isdigit() else s
    return str(value)
