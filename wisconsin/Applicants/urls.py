from django.urls import path

from . import views
from . import builder_views

urlpatterns = [
    path("", views.portal_view, name="applicants_home"),
    path("applications/<int:app_id>/next-steps.pdf", views.download_next_steps_pdf, name="applicants_next_steps_pdf"),
    path("applications/<int:app_id>/application.pdf", views.download_application_pdf, name="applicants_application_pdf"),
    path("applications/<int:app_id>/offline-application.pdf", views.download_offline_application_pdf, name="applicants_offline_application_pdf"),
    path("validate-field/", views.validate_field_view, name="applicants_validate_field"),
    path("autosave-field/", views.autosave_dynamic_field, name="applicants_autosave_field"),
    path("api/states/", views.api_get_states, name="applicants_api_states"),
    path("api/cities/", views.api_get_cities, name="applicants_api_cities"),
    path("offer/", views.offer_action, name="applicants_offer_action"),
    path("deposit/", views.deposit_payment, name="applicants_deposit_payment"),

    # Applicant notification bell (AJAX)
    path("notifications/", views.applicant_notifications_page, name="applicant_notifications"),
    path("notifications/recent/", views.applicant_notifications_recent, name="applicant_notifications_recent"),
    path("notifications/read-all/", views.applicant_notifications_mark_all, name="applicant_notifications_mark_all"),
    path("notifications/<int:notification_id>/read/", views.applicant_notifications_mark_read, name="applicant_notifications_mark_read"),
    path("notifications/<int:notification_id>/delete/", views.applicant_notifications_delete, name="applicant_notifications_delete"),

    # ── Stripe Payment ─────────────────────────────────────────
    path("payments/stripe/success/", views.stripe_checkout_success, name="applicants_stripe_success"),
    path("payments/stripe/cancel/", views.stripe_checkout_cancel, name="applicants_stripe_cancel"),
    path("payments/stripe/webhook/", views.stripe_webhook, name="applicants_stripe_webhook"),

    # ── Builder Admin ──────────────────────────────────────────
    path("builder/", builder_views.dashboard, name="builder_dashboard"),
    path("builder/forms/new/", builder_views.form_create, name="builder_form_create"),
    path("builder/forms/<int:form_id>/edit/", builder_views.form_edit, name="builder_form_edit"),
    path("builder/forms/<int:form_id>/json/", builder_views.form_json, name="builder_form_json"),
    path("builder/forms/<int:form_id>/delete/", builder_views.form_delete, name="builder_form_delete"),
    path("builder/forms/<int:form_id>/clone/", builder_views.form_clone, name="builder_form_clone"),
    path("builder/forms/<int:form_id>/preview/", builder_views.form_preview, name="builder_form_preview"),
    path("builder/forms/<int:form_id>/assignments/", builder_views.assignments, name="builder_assignments"),
    path("builder/assignments/<int:assignment_id>/delete/", builder_views.assignment_delete, name="builder_assignment_delete"),
    path("builder/forms/<int:form_id>/section-assignments/", builder_views.section_assignments, name="builder_section_assignments"),
    path("builder/section-assignments/<int:assignment_id>/delete/", builder_views.section_assignment_delete, name="builder_section_assignment_delete"),
    path("builder/forms/<int:form_id>/reorder-sections/", builder_views.reorder_sections, name="builder_reorder_sections"),
    path("builder/forms/<int:form_id>/sections/add/", builder_views.section_add, name="builder_section_create"),
    path("builder/sections/<int:section_id>/edit/", builder_views.section_edit, name="builder_section_edit"),
    path("builder/sections/<int:section_id>/json/", builder_views.section_json, name="builder_section_json"),
    path("builder/sections/<int:section_id>/delete/", builder_views.section_delete, name="builder_section_delete"),
    path("builder/sections/<int:section_id>/clone/", builder_views.section_clone, name="builder_section_clone"),
    path("builder/sections/<int:section_id>/reorder-fields/", builder_views.reorder_fields, name="builder_reorder_fields"),
    path("builder/forms/<int:form_id>/fields/add/", builder_views.field_add_form, name="builder_field_create"),
    path("builder/fields/<int:field_id>/edit/", builder_views.field_edit, name="builder_field_edit"),
    path("builder/fields/<int:field_id>/json/", builder_views.field_json, name="builder_field_json"),
    path("builder/fields/<int:field_id>/delete/", builder_views.field_delete, name="builder_field_delete"),
    path("builder/fields/<int:field_id>/clone/", builder_views.field_clone, name="builder_field_clone"),
    path("builder/fields/<int:field_id>/choices/add/", builder_views.choice_add, name="builder_choice_add"),
    path("builder/choices/<int:choice_id>/delete/", builder_views.choice_delete, name="builder_choice_delete"),
    path("builder/fields/<int:field_id>/validation/add/", builder_views.validation_add, name="builder_validation_add"),
    path("builder/validation/<int:rule_id>/delete/", builder_views.validation_delete, name="builder_validation_delete"),
    path("builder/fields/<int:field_id>/visibility/add/", builder_views.visibility_add, name="builder_visibility_add"),
    path("builder/visibility/<int:rule_id>/delete/", builder_views.visibility_delete, name="builder_visibility_delete"),
    path("builder/forms/<int:form_id>/logic/add/", builder_views.logic_create, name="builder_logic_create"),
    path("builder/logic/<int:rule_id>/delete/", builder_views.logic_delete, name="builder_logic_delete"),
    path("builder/forms/<int:form_id>/api/fields/", builder_views.api_form_fields, name="builder_api_form_fields"),
    path("builder/forms/<int:form_id>/api/preview/", builder_views.api_form_preview_data, name="builder_api_form_preview"),
    path("builder/workflows/", builder_views.workflow_list, name="builder_workflow_list"),
    path("builder/workflows/new/", builder_views.workflow_create, name="builder_workflow_create"),
    path("builder/workflows/<int:workflow_id>/edit/", builder_views.workflow_edit, name="builder_workflow_edit"),
    path("builder/workflows/<int:workflow_id>/delete/", builder_views.workflow_delete, name="builder_workflow_delete"),
    path("builder/workflows/<int:workflow_id>/steps/add/", builder_views.workflow_step_add, name="builder_workflow_step_add"),
    path("builder/steps/<int:step_id>/edit/", builder_views.workflow_step_edit, name="builder_workflow_step_edit"),
    path("builder/steps/<int:step_id>/delete/", builder_views.workflow_step_delete, name="builder_workflow_step_delete"),
    path("builder/steps/<int:step_id>/conditions/add/", builder_views.workflow_step_condition_add, name="builder_workflow_step_condition_add"),
    path("builder/conditions/<int:condition_id>/delete/", builder_views.workflow_step_condition_delete, name="builder_workflow_step_condition_delete"),

    # ── Builder Cycles ─────────────────────────────────────────
    path("builder/cycles/", builder_views.cycle_list, name="builder_cycle_list"),
    path("builder/cycles/new/", builder_views.cycle_create, name="builder_cycle_create"),
    path("builder/cycles/<int:cycle_id>/edit/", builder_views.cycle_edit, name="builder_cycle_edit"),
    path("builder/cycles/<int:cycle_id>/delete/", builder_views.cycle_delete, name="builder_cycle_delete"),

    # ── Builder Fees ───────────────────────────────────────────
    path("builder/fees/", builder_views.fee_list, name="builder_fee_list"),
    path("builder/fees/new/", builder_views.fee_create, name="builder_fee_create"),
    path("builder/fees/<int:fee_id>/edit/", builder_views.fee_edit, name="builder_fee_edit"),
    path("builder/fees/<int:fee_id>/delete/", builder_views.fee_delete, name="builder_fee_delete"),

    # ── Builder Applicant Type Requirements ────────────────────
    path("builder/req-types/", builder_views.req_type_list, name="builder_req_type_list"),
    path("builder/req-types/new/", builder_views.req_type_create, name="builder_req_type_create"),
    path("builder/req-types/<int:req_id>/edit/", builder_views.req_type_edit, name="builder_req_type_edit"),
    path("builder/req-types/<int:req_id>/delete/", builder_views.req_type_delete, name="builder_req_type_delete"),

    # ── Builder Document Requirements ──────────────────────────
    path("builder/doc-reqs/", builder_views.doc_req_list, name="builder_doc_req_list"),
    path("builder/doc-reqs/new/", builder_views.doc_req_create, name="builder_doc_req_create"),
    path("builder/doc-reqs/<int:doc_req_id>/edit/", builder_views.doc_req_edit, name="builder_doc_req_edit"),
    path("builder/doc-reqs/<int:doc_req_id>/delete/", builder_views.doc_req_delete, name="builder_doc_req_delete"),
]
