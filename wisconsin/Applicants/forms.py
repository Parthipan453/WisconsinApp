import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

from django import forms
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
)

from .models import FIELD_TYPE_CHOICES, FormField, FieldChoice, ValidationRule, VisibilityRule


INPUT_ATTRS = {"class": "uw-input auth-input"}

FIRST_NAME_VALIDATOR = RegexValidator(
    regex=r"^[a-zA-Z\s\'-]{3,50}$",
    message="Enter valid name.",
)
LAST_NAME_VALIDATOR = RegexValidator(
    regex=r"^[a-zA-Z\s\'-]{1,50}$",
    message="Enter valid name.",
)
PASSWORD_VALIDATOR = RegexValidator(
    regex=r"^(?=.*[A-Za-z])(?=.*\d).{6,}$",
    message="At least 6 characters with letters and numbers.",
)


 

FIELD_VALIDATORS: dict[str, dict] = {
    "text": {
        "regex": r"^[\w\s\-'\"\,\.\#\&\/\(\)\!\?\:\;]{1,500}$",
        "msg": "Enter valid value.",
    },
    "email": {
        "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "msg": "Enter valid email.",
    },
    "phone": {
        "regex": r"^\+?1?\d{7,15}$",
        "msg": "Enter valid phone.",
    },
    "url": {
        "regex": r"^https?:\/\/[\w\-\.]+\.\w{2,}[\w\-\.~:\/?#\[\]@!$&'()*+,;=]*$",
        "msg": "Enter valid URL.",
    },
    "password": {
        "regex": r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$",
        "msg": "Enter valid password.",
    },
    "ssn": {
        "regex": r"^\d{3}-\d{2}-\d{4}$",
        "msg": "Enter valid SSN.",
    },
    "textarea": {
        "regex": r"^[\w\s\-'\"\,\.\#\&\/\(\)\!\?\:\;\n\r]{1,10000}$",
        "msg": "Enter valid value.",
    },
    "rich_text": {
        "regex": r"^[\w\s\-'\"\,\.\#\&\/\(\)\!\?\:\;\n\r<>=/\\]{0,50000}$",
        "msg": "Enter valid value.",
    },
    "state": {
        "regex": r"^[a-zA-Z\s\'-]{2,100}$",
        "msg": "Enter valid state.",
    },
    "country": {
        "regex": r"^[a-zA-Z\s\'-]{2,100}$",
        "msg": "Enter valid country.",
    },
    "city": {
        "regex": r"^[a-zA-Z\s\'-]{2,100}$",
        "msg": "Enter valid city.",
    },
    "first_name": {
        "regex": r"^[a-zA-Z\s\'-]{3,50}$",
        "msg": "Enter valid name.",
    },
    "last_name": {
        "regex": r"^[a-zA-Z\s\'-]{1,50}$",
        "msg": "Enter valid name.",
    },
    "year": {
        "regex": r"^\d{4}$",
        "msg": "Enter a valid 4-digit year.",
    },
}

_NAME_CODES_F = {"first_name", "firstname", "given_name"}
_LAST_CODES_F = {"last_name", "lastname", "family_name"}


def _detect_name_type(field_code: str, field_label: str):
    code_lower = field_code.lower().replace(" ", "_")
    label_lower = field_label.lower().replace(" ", "_")
    if any(c in code_lower or c in label_lower for c in _NAME_CODES_F):
        if any(c in code_lower or c in label_lower for c in ("last", "family")):
            return "last_name"
        return "first_name"
    if any(c in code_lower or c in label_lower for c in _LAST_CODES_F):
        return "last_name"
    return None


def _default_field_validators(field_type: str, field=None) -> list[RegexValidator]:
    actual_type = field_type
    if field_type == "text" and field:
        name_type = _detect_name_type(field.code, field.label)
        if name_type:
            actual_type = name_type
    cfg = FIELD_VALIDATORS.get(actual_type)
    if cfg:
        return [RegexValidator(regex=cfg["regex"], message=cfg["msg"])]
    return []


def _resolve_date_value(value_str: str) -> Optional[date]:
    if not value_str:
        return None
    value_str = str(value_str).strip()
    if value_str == "today":
        return date.today()
    m = re.match(r"^today\s*([+-])\s*(\d+)\s*([ymd])$", value_str)
    if m:
        op, num, unit = m.group(1), int(m.group(2)), m.group(3)
        today = date.today()
        if unit == "y":
            try:
                return today.replace(year=today.year - num if op == "-" else today.year + num)
            except ValueError:
                return today.replace(year=today.year - num if op == "-" else today.year + num,
                                     month=1, day=1)
        if unit == "m":
            m_offset = -num if op == "-" else num
            total_months = today.year * 12 + (today.month - 1) + m_offset
            return date(total_months // 12, total_months % 12 + 1, min(today.day, 28))
        if unit == "d":
            return today + timedelta(days=-num if op == "-" else num)
    try:
        return datetime.strptime(value_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        pass
    try:
        return datetime.strptime(value_str, "%Y").date()
    except (ValueError, TypeError):
        pass
    return None


def _get_date_attrs(field) -> dict[str, str]:
    attrs = {}
    for rule in field.validations.filter(is_active=True):
        if rule.validation_type == "min_value":
            d = _resolve_date_value(rule.value)
            if d:
                attrs["min"] = d.isoformat()
        elif rule.validation_type == "max_value":
            d = _resolve_date_value(rule.value)
            if d:
                attrs["max"] = d.isoformat()
    return attrs


 

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "you@example.edu",
                "autocomplete": "email",
                "data-live-regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "data-live-msg": "Enter valid email.",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
                "data-live-regex": r"^(?=.*[A-Za-z])(?=.*\d).{6,}$",
                "data-live-msg": "Enter valid password.",
            }
        ),
        min_length=6,
        validators=[PASSWORD_VALIDATOR],
    )


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label="First name",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "Jane",
                "autocomplete": "given-name",
                "data-live-regex": r"^[a-zA-Z\s\'-]{3,50}$",
                "data-live-msg": "Enter valid name.",
            }
        ),
        validators=[FIRST_NAME_VALIDATOR],
    )
    last_name = forms.CharField(
        label="Last name",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "Doe",
                "autocomplete": "family-name",
                "data-live-regex": r"^[a-zA-Z\s\'-]{1,50}$",
                "data-live-msg": "Enter valid name.",
            }
        ),
        validators=[LAST_NAME_VALIDATOR],
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "you@example.edu",
                "autocomplete": "email",
                "data-live-regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "data-live-msg": "Enter valid email.",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "At least 6 characters",
                "autocomplete": "new-password",
                "data-live-regex": r"^(?=.*[A-Za-z])(?=.*\d).{6,}$",
                "data-live-msg": "Enter valid password.",
                "data-password-checklist": "true",
            }
        ),
        min_length=6,
        validators=[PASSWORD_VALIDATOR],
    )
    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                **INPUT_ATTRS,
                "placeholder": "Re-enter your password",
                "autocomplete": "new-password",
                "data-match": "password",
                "data-live-msg": "Enter valid password.",
            }
        ),
    )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


 

class DynamicForm(forms.Form):
    """Builds a Django Form dynamically from FormSection metadata."""

    def __init__(
        self,
        section,
        response_data: Optional[dict[str, Any]] = None,
        *args,
        dob_min_year: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.section = section
        self._comparison_rules = []
        self._dob_min_year = dob_min_year
        self._build_fields(response_data or {})

    def _build_fields(self, response_data: dict[str, Any]) -> None:
        fields = (
            FormField.objects.filter(section=self.section, is_active=True)
            .order_by("sort_order")
            .prefetch_related("choices", "validations")
        )
        for field in fields:
            form_field = self._create_form_field(field, response_data)
            if form_field is not None:
                self.fields[field.code] = form_field
            for rule in field.validations.filter(is_active=True):
                if rule.validation_type == "custom" and rule.value.startswith("field_comparison:"):
                    parts = rule.value.split(":")
                    self._comparison_rules.append({
                        "source": field.code,
                        "target": parts[1],
                        "op": parts[2] if len(parts) > 2 else "lte",
                    })
                    if form_field is not None and hasattr(form_field, "widget"):
                        form_field.widget.attrs["data-field-compare"] = parts[1]
                        form_field.widget.attrs["data-field-compare-op"] = parts[2] if len(parts) > 2 else "lte"
        self._apply_dob_min_year()

    def clean(self):
        cleaned = super().clean()
        for rule in self._comparison_rules:
            src = cleaned.get(rule["source"])
            tgt = cleaned.get(rule["target"])
            if src is None or src == "" or tgt is None or tgt == "":
                continue
            op = rule["op"]
            valid = False
            if op == "lte":
                valid = float(src) <= float(tgt)
            elif op == "lt":
                valid = float(src) < float(tgt)
            elif op == "gte":
                valid = float(src) >= float(tgt)
            elif op == "gt":
                valid = float(src) > float(tgt)
            elif op == "eq":
                valid = float(src) == float(tgt)
            if not valid:
                labels = {
                    "lte": "cannot be later than",
                    "lt": "must be before",
                    "gte": "must be at least",
                    "gt": "must be after",
                    "eq": "must equal",
                }
                target_label = rule["target"].replace("_", " ").title()
                msg = f"{labels.get(op, 'is invalid compared to')} {target_label}"
                self.add_error(rule["source"], msg)
        return cleaned

    def _apply_dob_min_year(self) -> None:
        if self._dob_min_year is None:
            return
        for code, field in self.fields.items():
            if isinstance(field, forms.IntegerField) and not isinstance(field, forms.FloatField) and hasattr(field, "widget") and isinstance(field.widget, forms.NumberInput):
                attrs = field.widget.attrs
                current_min = int(float(str(attrs.get("min", "1900")).split("-")[0]))
                if current_min < self._dob_min_year:
                    attrs["min"] = str(self._dob_min_year)
                    new_validators = []
                    for v in field.validators:
                        if isinstance(v, MinValueValidator):
                            new_validators.append(MinValueValidator(self._dob_min_year))
                        else:
                            new_validators.append(v)
                    field.validators = new_validators

    def _create_form_field(
        self,
        field: FormField,
        response_data: dict[str, Any],
    ) -> Optional[forms.Field]:
        field_type = field.field_type

        if not self._is_field_visible(field, response_data):
            return None

        is_required = self._is_field_required(field, response_data)

        kwargs: dict[str, Any] = {
            "label": field.label,
            "required": is_required,
            "help_text": field.help_text or "",
        }

        base_attrs = {"data-field-code": field.code}
        builder = FIELD_TYPE_BUILDERS.get(field_type, FIELD_TYPE_BUILDERS["text"])

        form_field = builder(field, kwargs, base_attrs)

        if form_field is not None and hasattr(form_field, "widget"):
            form_field.widget.attrs["data-field-id"] = field.pk
            form_field.widget.attrs["data-field-type"] = field.field_type

            if not form_field.validators:
                form_field.validators.extend(
                    _default_field_validators(field_type, field)
                )

            self._attach_live_regex(form_field, field, field_type)

        return form_field

    _STRING_FIELD_TYPES = {"text", "textarea", "rich_text", "email", "url",
                            "password", "ssn", "phone", "city", "state",
                            "country", "first_name", "last_name"}

    def _attach_live_regex(
        self,
        form_field: forms.Field,
        field: FormField,
        field_type: str,
    ) -> None:
        name_type = _detect_name_type(field.code, field.label) if field_type == "text" else None
        if name_type:
            cfg = FIELD_VALIDATORS[name_type]
            form_field.widget.attrs["data-live-regex"] = cfg["regex"]
            form_field.widget.attrs["data-live-msg"] = cfg["msg"]
            self._ensure_validator(form_field, cfg["regex"], cfg["msg"])
            return

        db_regex = field.validations.filter(
            validation_type="regex", is_active=True
        ).first()
        if db_regex and db_regex.value:
            form_field.widget.attrs["data-live-regex"] = db_regex.value
            if field_type in self._STRING_FIELD_TYPES:
                self._ensure_validator(
                    form_field, db_regex.value,
                    db_regex.error_message or "Enter a valid value.",
                )
            msg_rule = field.validations.filter(
                validation_type="regex_msg", is_active=True
            ).first()
            if msg_rule and msg_rule.value:
                form_field.widget.attrs["data-live-msg"] = msg_rule.value
        else:
            cfg = FIELD_VALIDATORS.get(field_type)
            if cfg:
                form_field.widget.attrs.setdefault("data-live-regex", cfg["regex"])
                form_field.widget.attrs.setdefault("data-live-msg", cfg["msg"])

    def _ensure_validator(self, form_field, pattern: str, message: str) -> None:
        if not any(
            isinstance(v, RegexValidator) and v.regex.pattern == pattern
            for v in form_field.validators
        ):
            form_field.validators.append(
                RegexValidator(regex=pattern, message=message)
            )

    @staticmethod
    def _normalize(v: Any) -> str:
        s = str(v).lower()
        if s in ("true", "on", "yes", "1"):
            return "yes"
        if s in ("false", "off", "no", "0", ""):
            return "no"
        return s

    def _rule_matches(self, rule: VisibilityRule, response_data: dict[str, Any]) -> bool:
        target_code = rule.target_field.code
        target_value = None
        found = False
        if self.data:
            if target_code in self.data:
                target_value = self.data.get(target_code)
                found = True
        if not found and response_data:
            if target_code in response_data:
                target_value = response_data.get(target_code)
                found = True
        if target_value is None:
            target_value = ""
        nv = self._normalize(target_value)
        nr = self._normalize(rule.value)
        if not found:
            return True
        if rule.operator == "eq":
            return nv == nr
        if rule.operator == "neq":
            return nv != nr
        if rule.operator == "not_empty":
            return bool(target_value) and str(target_value).strip() != ""
        if rule.operator == "is_empty":
            return not target_value or str(target_value).strip() == ""
        if rule.operator == "contains":
            return nr in nv
        if rule.operator == "gt":
            try:
                return float(nv) > float(nr)
            except (ValueError, TypeError):
                return False
        if rule.operator == "gte":
            try:
                return float(nv) >= float(nr)
            except (ValueError, TypeError):
                return False
        if rule.operator == "lt":
            try:
                return float(nv) < float(nr)
            except (ValueError, TypeError):
                return False
        if rule.operator == "lte":
            try:
                return float(nv) <= float(nr)
            except (ValueError, TypeError):
                return False
        if rule.operator == "in":
            return nv in [x.strip() for x in nr.split(",")]
        if rule.operator == "not_in":
            return nv not in [x.strip() for x in nr.split(",")]
        if rule.operator == "checked":
            return nv == "yes"
        if rule.operator == "not_checked":
            return nv == "no"
        return False

    def _group_matches(self, rules_group, response_data: dict[str, Any]) -> bool:
        and_rules = [r for r in rules_group if r.logic_operator == "AND"]
        or_rules = [r for r in rules_group if r.logic_operator == "OR"]
        if and_rules and not all(
            self._rule_matches(r, response_data) for r in and_rules
        ):
            return False
        if or_rules and not any(
            self._rule_matches(r, response_data) for r in or_rules
        ):
            return False
        return True

    def _is_field_visible(self, field: FormField, response_data: dict[str, Any]) -> bool:
        rules = list(VisibilityRule.objects.filter(field=field, is_active=True))
        if not rules:
            return True
        show_rules = [r for r in rules if r.action == "show"]
        hide_rules = [r for r in rules if r.action == "hide"]

        # Hide actions: a matching hide rule hides the field.
        for r in hide_rules:
            if self._rule_matches(r, response_data):
                return False
        # Show actions: field is visible by default unless show rules exist and none match.
        if show_rules:
            return self._group_matches(show_rules, response_data)
        return True

    def _is_field_required(self, field: FormField, response_data: dict[str, Any]) -> bool:
        """Base required + conditional require/optional actions."""
        required = field.is_required or field.validations.filter(
            validation_type="required", is_active=True
        ).exists()
        rules = list(
            VisibilityRule.objects.filter(
                field=field, is_active=True, action__in=("require", "optional")
            )
        )
        for r in rules:
            if self._rule_matches(r, response_data):
                required = True if r.action == "require" else False
        return required

    @staticmethod
    def _get_validation_value(field: FormField, vtype: str) -> Optional[str]:
        rule = field.validations.filter(
            validation_type=vtype, is_active=True
        ).first()
        return rule.value if rule else None


 

def _build_text(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(
        attrs={"class": "uw-input", "placeholder": field.placeholder or "", **attrs}
    )
    kwargs["max_length"] = DynamicForm._get_validation_value(field, "max_length") or 500
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("text", field)
    return forms.CharField(**kwargs)


def _build_textarea(field, kwargs, attrs):
    rows = field.rows or 4
    kwargs["widget"] = forms.Textarea(
        attrs={"class": "uw-input", "placeholder": field.placeholder or "", "rows": rows, **attrs}
    )
    kwargs["max_length"] = DynamicForm._get_validation_value(field, "max_length") or 10000
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("textarea")
    return forms.CharField(**kwargs)


def _build_rich_text(field, kwargs, attrs):
    rows = field.rows or 8
    kwargs["widget"] = forms.Textarea(
        attrs={
            "class": "uw-input rich-text-editor",
            "placeholder": field.placeholder or "",
            "rows": rows,
            **attrs,
        }
    )
    kwargs["max_length"] = DynamicForm._get_validation_value(field, "max_length") or 50000
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("rich_text")
    return forms.CharField(**kwargs)


def _build_number(field, kwargs, attrs):
    kwargs["widget"] = forms.NumberInput(
        attrs={"class": "uw-input", "placeholder": field.placeholder or "", "step": "any", **attrs}
    )
    min_val = DynamicForm._get_validation_value(field, "min_value")
    max_val = DynamicForm._get_validation_value(field, "max_value")
    validators = []
    if min_val:
        kwargs["min_value"] = float(min_val)
        validators.append(MinValueValidator(float(min_val)))
    if max_val:
        kwargs["max_value"] = float(max_val)
        validators.append(MaxValueValidator(float(max_val)))
    if validators:
        kwargs["validators"] = kwargs.get("validators", []) + validators
    return forms.FloatField(**kwargs)


def _build_year(field, kwargs, attrs):
    date_attrs = _get_date_attrs(field)
    raw_min = str(date_attrs.get("min", "1900"))
    raw_max = str(date_attrs.get("max", "2099"))
    min_val = int(raw_min.split("-")[0])
    max_val = int(raw_max.split("-")[0])
    widget_attrs = {"class": "uw-input", "min": str(min_val), "max": str(max_val), **attrs}
    kwargs["widget"] = forms.HiddenInput(attrs=widget_attrs)

    def validate_ym(value):
        if not value:
            return value
        s = str(value)
        if "-" in s:
            parts = s.split("-")
            if len(parts) != 2:
                raise forms.ValidationError("Enter a valid year or year-month.")
            y, m = parts
            if not y.isdigit() or not m.isdigit():
                raise forms.ValidationError("Enter a valid year or year-month.")
            y, m = int(y), int(m)
            if y < min_val or y > max_val:
                raise forms.ValidationError(f"Year must be between {min_val} and {max_val}.")
            if m < 1 or m > 12:
                raise forms.ValidationError("Month must be between 01 and 12.")
        else:
            if not s.isdigit():
                raise forms.ValidationError("Enter a valid year.")
            y = int(s)
            if y < min_val or y > max_val:
                raise forms.ValidationError(f"Year must be between {min_val} and {max_val}.")
        return value

    kwargs["validators"] = kwargs.get("validators", []) + [validate_ym]
    return forms.CharField(**kwargs)


def _build_date(field, kwargs, attrs):
    date_attrs = _get_date_attrs(field)
    widget_attrs = {"class": "uw-input", "type": "date", **attrs}
    widget_attrs.update(date_attrs)
    kwargs["widget"] = forms.DateInput(attrs=widget_attrs)
    if "min" in date_attrs:
        kwargs["validators"] = kwargs.get("validators", []) + [MinValueValidator(date.fromisoformat(date_attrs["min"]))]
    if "max" in date_attrs:
        kwargs["validators"] = kwargs.get("validators", []) + [MaxValueValidator(date.fromisoformat(date_attrs["max"]))]
    return forms.DateField(**kwargs)


def _build_email(field, kwargs, attrs):
    kwargs["widget"] = forms.EmailInput(
        attrs={"class": "uw-input", "placeholder": field.placeholder or "email@example.com", **attrs}
    )
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("email")
    return forms.EmailField(**kwargs)


def _build_phone(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(
        attrs={"class": "uw-input", "type": "tel", "placeholder": field.placeholder or "", **attrs}
    )
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("phone")
    return forms.CharField(**kwargs)


def _build_url(field, kwargs, attrs):
    kwargs["widget"] = forms.URLInput(
        attrs={"class": "uw-input", "placeholder": field.placeholder or "https://", **attrs}
    )
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("url")
    return forms.URLField(**kwargs)


def _build_password(field, kwargs, attrs):
    kwargs["widget"] = forms.PasswordInput(
        attrs={"class": "uw-input", "placeholder": field.placeholder or "", **attrs}
    )
    kwargs["min_length"] = 8
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("password")
    return forms.CharField(**kwargs)


def _build_ssn(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(
        attrs={
            "class": "uw-input",
            "type": "password",
            "placeholder": field.placeholder or "XXX-XX-XXXX",
            "maxlength": "11",
            **attrs,
        }
    )
    kwargs["max_length"] = 11
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("ssn")
    return forms.CharField(**kwargs)


def _build_gpa(field, kwargs, attrs):
    kwargs["widget"] = forms.NumberInput(
        attrs={
            "class": "uw-input",
            "step": "0.01",
            "min": "0",
            "max": "4.0",
            "placeholder": field.placeholder or "e.g. 3.75",
            **attrs,
        }
    )
    kwargs["min_value"] = 0
    kwargs["max_value"] = 4.0
    kwargs["validators"] = kwargs.get("validators", []) + [
        MinValueValidator(0),
        MaxValueValidator(4.0),
    ]
    return forms.FloatField(**kwargs)


def _build_currency(field, kwargs, attrs):
    kwargs["widget"] = forms.NumberInput(
        attrs={
            "class": "uw-input",
            "step": "0.01",
            "min": "0",
            "placeholder": field.placeholder or "0.00",
            **attrs,
        }
    )
    kwargs["min_value"] = 0
    kwargs["validators"] = kwargs.get("validators", []) + [MinValueValidator(0)]
    return forms.FloatField(**kwargs)


def _build_select(field, kwargs, attrs):
    choices = _get_field_choices(field)
    has_empty = any(c.value == "" for c in choices)
    if has_empty:
        choice_list = [(c.value, c.label) for c in choices]
    else:
        choice_list = [("", f"Select {field.label}")] + [(c.value, c.label) for c in choices]
    kwargs["widget"] = forms.Select(attrs={"class": "uw-input", **attrs})
    kwargs["choices"] = choice_list
    return forms.ChoiceField(**kwargs)


def _build_radio(field, kwargs, attrs):
    choices = _get_field_choices(field)
    choice_list = [(c.value, c.label) for c in choices]
    kwargs["widget"] = forms.RadioSelect(attrs={**attrs})
    kwargs["choices"] = choice_list
    return forms.ChoiceField(**kwargs)


def _build_multi_select(field, kwargs, attrs):
    choices = _get_field_choices(field)
    choice_list = [(c.value, c.label) for c in choices]
    kwargs["widget"] = forms.SelectMultiple(attrs={"class": "uw-input", **attrs})
    kwargs["choices"] = choice_list
    return forms.MultipleChoiceField(**kwargs)


def _build_checkbox(field, kwargs, attrs):
    kwargs["widget"] = forms.CheckboxInput(attrs={**attrs})
    kwargs["required"] = False
    return forms.BooleanField(**kwargs)


def _build_file(field, kwargs, attrs):
    kwargs["widget"] = forms.FileInput(attrs={"class": "uw-input", **attrs})
    kwargs["required"] = kwargs.get("required", False)
    return forms.FileField(**kwargs)


def _build_hidden(field, kwargs, attrs):
    kwargs["widget"] = forms.HiddenInput(attrs={**attrs})
    kwargs["required"] = False
    return forms.CharField(**kwargs)


def _build_country(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(
        attrs={
            "class": "uw-input",
            "placeholder": field.placeholder or "United States",
            "autocomplete": "off",
            "data-country-search": "true",
            **attrs,
        }
    )
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("country")
    return forms.CharField(**kwargs)


def _build_state(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(
        attrs={
            "class": "uw-input",
            "placeholder": field.placeholder or "Wisconsin",
            "autocomplete": "off",
            **attrs,
        }
    )
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("state")
    return forms.CharField(**kwargs)


def _build_city(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(
        attrs={
            "class": "uw-input",
            "placeholder": field.placeholder or "Madison",
            "autocomplete": "off",
            **attrs,
        }
    )
    kwargs["validators"] = kwargs.get("validators", []) + _default_field_validators("city")
    return forms.CharField(**kwargs)


def _build_text_fallback(field, kwargs, attrs):
    kwargs["widget"] = forms.TextInput(attrs={"class": "uw-input", **attrs})
    return forms.CharField(**kwargs)


FIELD_TYPE_BUILDERS = {
    "text": _build_text,
    "heading": _build_hidden,
    "textarea": _build_textarea,
    "rich_text": _build_rich_text,
    "number": _build_number,
    "date": _build_date,
    "email": _build_email,
    "phone": _build_phone,
    "url": _build_url,
    "password": _build_password,
    "ssn": _build_ssn,
    "gpa": _build_gpa,
    "currency": _build_currency,
    "select": _build_select,
    "radio": _build_radio,
    "multi_select": _build_multi_select,
    "checkbox": _build_checkbox,
    "file": _build_file,
    "hidden": _build_hidden,
    "country": _build_country,
    "state": _build_state,
    "city": _build_city,
    "year": _build_year,
}


def _get_field_choices(field: FormField) -> list[FieldChoice]:
    return list(
        FieldChoice.objects.filter(field=field, is_active=True).order_by("sort_order")
    )
