from django import forms
from django.utils import timezone
from Faculty.leo.models import (
    ResearchMilestone,
    ResearchMilestoneSubmission,
)
from Students.models import (
    DissertationProposal,
    ResearchPublication,
    FinalDissertationSubmission,
)


class DissertationProposalForm(forms.ModelForm):

    class Meta:
        model = DissertationProposal

        fields = [
            "proposal_title",
            "abstract",
            "proposal_file",
        ]

        widgets = {
            "proposal_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter dissertation proposal title",
                }
            ),
            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter dissertation proposal abstract",
                    "rows": 6,
                }
            ),
            "proposal_file": forms.FileInput(
                attrs={
                    "id": "proposalFileInput",
                    "class": "d-none",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        self.phd_student = kwargs.pop(
            "phd_student",
            None,
        )

        self.coursework_completed = kwargs.pop(
            "coursework_completed",
            False,
        )

        self.preliminary_exam_passed = kwargs.pop(
            "preliminary_exam_passed",
            False,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.phd_student is None:
            raise ValueError(
                "DissertationProposalForm requires a PhD student instance."
            )

        self.fields["proposal_title"].label = "Proposal Title"
        self.fields["abstract"].label = "Abstract"
        self.fields["proposal_file"].label = "Proposal Document"

        self.fields["proposal_title"].required = True
        self.fields["abstract"].required = True
        self.fields["proposal_file"].required = not bool(
            self.instance.pk and self.instance.proposal_file
        )

    def clean_proposal_title(self):

        proposal_title = self.cleaned_data.get(
            "proposal_title",
        )

        if not proposal_title:
            raise forms.ValidationError("Please enter the proposal title.")

        proposal_title = proposal_title.strip()

        if len(proposal_title) < 5:
            raise forms.ValidationError(
                "Proposal title must contain at least 5 characters."
            )

        if len(proposal_title) > 255:
            raise forms.ValidationError("Proposal title cannot exceed 255 characters.")

        return proposal_title

    def clean_abstract(self):

        abstract = self.cleaned_data.get(
            "abstract",
        )

        if not abstract:
            raise forms.ValidationError("Please enter the proposal abstract.")

        abstract = abstract.strip()

        if len(abstract) < 50:
            raise forms.ValidationError("Abstract must contain at least 50 characters.")

        return abstract

    def clean_proposal_file(self):

        proposal_file = self.cleaned_data.get(
            "proposal_file",
        )

        if not proposal_file:

            if self.instance.pk and self.instance.proposal_file:
                return self.instance.proposal_file

            raise forms.ValidationError(
                "Please upload your dissertation proposal file."
            )

        allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
        }

        file_name = proposal_file.name

        extension = ""

        if "." in file_name:
            extension = file_name[file_name.rfind(".") :].lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError("Only PDF, DOC and DOCX files are allowed.")

        max_size = 100 * 1024 * 1024

        if proposal_file.size > max_size:
            raise forms.ValidationError("File size cannot exceed 100 MB.")

        return proposal_file

    def clean(self):

        cleaned_data = super().clean()

        if not self.coursework_completed:

            raise forms.ValidationError(
                "You must complete the required coursework credits before creating a dissertation proposal."
            )

        if not self.preliminary_exam_passed:

            raise forms.ValidationError(
                "You must pass the Preliminary / Qualifying Examination before creating a dissertation proposal."
            )

        existing_proposal = (
            DissertationProposal.objects.filter(
                phd_student=self.phd_student,
            )
            .exclude(
                pk=self.instance.pk,
            )
            .first()
        )

        if existing_proposal:

            raise forms.ValidationError("You already have a dissertation proposal.")

        return cleaned_data

    def save(self, commit=True):

        proposal = super().save(
            commit=False,
        )

        proposal.phd_student = self.phd_student

        if not proposal.pk:

            proposal.status = "DRAFT"
            proposal.advisor_review_status = "PENDING"
            proposal.result = "PENDING"
            proposal.resubmission_count = 0

        if commit:
            proposal.save()

        return proposal


class ResearchMilestoneSubmissionForm(forms.ModelForm):

    class Meta:
        model = ResearchMilestoneSubmission

        fields = [
            "main_document",
            "additional_file_1",
            "additional_file_2",
            "additional_file_3",
            "student_remarks",
        ]

        widgets = {
            "main_document": forms.FileInput(
                attrs={
                    "id": "researchMainDocumentInput",
                    "class": "d-none",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "additional_file_1": forms.FileInput(
                attrs={
                    "id": "researchAdditionalFile1Input",
                    "class": "d-none",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "additional_file_2": forms.FileInput(
                attrs={
                    "id": "researchAdditionalFile2Input",
                    "class": "d-none",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "additional_file_3": forms.FileInput(
                attrs={
                    "id": "researchAdditionalFile3Input",
                    "class": "d-none",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "student_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Enter any remarks related to your research submission",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        self.phd_student = kwargs.pop(
            "phd_student",
            None,
        )

        self.milestone = kwargs.pop(
            "milestone",
            None,
        )

        self.is_resubmission = kwargs.pop(
            "is_resubmission",
            False,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.phd_student is None:
            raise ValueError(
                "ResearchMilestoneSubmissionForm requires a PhD student instance."
            )

        if self.milestone is None:
            raise ValueError(
                "ResearchMilestoneSubmissionForm requires a research milestone instance."
            )

        self.fields["main_document"].label = "Research Document"

        self.fields["additional_file_1"].label = "Additional Document 1"

        self.fields["additional_file_2"].label = "Additional Document 2"

        self.fields["additional_file_3"].label = "Additional Document 3"

        self.fields["student_remarks"].label = "Student Remarks"

        self.fields["main_document"].required = True

        self.fields["additional_file_1"].required = False

        self.fields["additional_file_2"].required = False

        self.fields["additional_file_3"].required = False

        self.fields["student_remarks"].required = False

    def clean_main_document(self):

        main_document = self.cleaned_data.get(
            "main_document",
        )

        if not main_document:
            raise forms.ValidationError("Please upload the research document.")

        self._validate_file(
            main_document,
            "Research document",
        )

        return main_document

    def clean_additional_file_1(self):

        additional_file = self.cleaned_data.get(
            "additional_file_1",
        )

        if additional_file:
            self._validate_file(
                additional_file,
                "Additional document 1",
            )

        return additional_file

    def clean_additional_file_2(self):

        additional_file = self.cleaned_data.get(
            "additional_file_2",
        )

        if additional_file:
            self._validate_file(
                additional_file,
                "Additional document 2",
            )

        return additional_file

    def clean_additional_file_3(self):

        additional_file = self.cleaned_data.get(
            "additional_file_3",
        )

        if additional_file:
            self._validate_file(
                additional_file,
                "Additional document 3",
            )

        return additional_file

    def clean_student_remarks(self):

        student_remarks = self.cleaned_data.get(
            "student_remarks",
        )

        if student_remarks:
            student_remarks = student_remarks.strip()

        if student_remarks and len(student_remarks) > 5000:
            raise forms.ValidationError(
                "Student remarks cannot exceed 5000 characters."
            )

        return student_remarks

    def _validate_file(
        self,
        uploaded_file,
        field_label,
    ):

        allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
        }

        file_name = uploaded_file.name

        extension = ""

        if "." in file_name:
            extension = file_name[file_name.rfind(".") :].lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                f"{field_label} must be a PDF, DOC or DOCX file."
            )

        max_size = 100 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(f"{field_label} cannot exceed 100 MB.")

    def clean(self):

        cleaned_data = super().clean()

        if self.milestone is None:
            return cleaned_data

        if self.phd_student is None:
            raise forms.ValidationError("A valid PhD student is required.")

        if self.milestone.phd_student != self.phd_student:
            raise forms.ValidationError(
                "This research milestone does not belong to you."
            )

        if self.milestone.status == "COMPLETED":
            raise forms.ValidationError(
                "This research milestone has already been completed."
            )

        if self.milestone.status == "ON_HOLD":
            raise forms.ValidationError("This research milestone is currently on hold.")

        if self.milestone.status not in [
            "PENDING",
            "IN_PROGRESS",
        ]:
            raise forms.ValidationError(
                "This research milestone is not currently active for submission."
            )

        latest_submission = (
            ResearchMilestoneSubmission.objects.filter(
                milestone=self.milestone,
            )
            .order_by(
                "-submission_number",
            )
            .first()
        )

        if latest_submission is None:

            if self.is_resubmission:
                raise forms.ValidationError(
                    "A resubmission cannot be created without a previous submission."
                )

            return cleaned_data

        if latest_submission.status in [
            "SUBMITTED",
            "UNDER_REVIEW",
        ]:

            raise forms.ValidationError(
                "Your latest research submission is currently under evaluation."
            )

        if latest_submission.status == "REVISION_REQUIRED":

            if not self.is_resubmission:
                raise forms.ValidationError(
                    "Revision is required before submitting the next research version."
                )

            return cleaned_data

        if latest_submission.status == "EVALUATED":

            if self.is_resubmission:
                raise forms.ValidationError(
                    "Resubmission is allowed only after faculty evaluation requires a revision."
                )

            raise forms.ValidationError(
                "Your latest research submission has already been evaluated."
            )

        if self.is_resubmission:
            raise forms.ValidationError(
                "Resubmission is allowed only after a revision is required."
            )

        return cleaned_data

    def save(self, commit=True):

        submission = super().save(
            commit=False,
        )

        submission.milestone = self.milestone

        if not submission.pk:

            last_submission = (
                ResearchMilestoneSubmission.objects.filter(
                    milestone=self.milestone,
                )
                .order_by(
                    "-submission_number",
                )
                .first()
            )

            submission.submission_number = (
                last_submission.submission_number + 1 if last_submission else 1
            )

            submission.status = "SUBMITTED"

        if commit:
            submission.save()

        return submission


class ResearchPublicationForm(forms.ModelForm):

    class Meta:
        model = ResearchPublication

        fields = [
            "milestone",
            "title",
            "publication_type",
            "authors",
            "journal",
            "abstract",
            "keywords",
            "publication_date",
            "publication_status",
            "doi",
            "indexed_status",
            "indexing_database",
            "manuscript_file",
            "acceptance_letter",
            "supporting_document",
            "student_remarks",
        ]

        widgets = {
            "milestone": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter publication title",
                    "autocomplete": "off",
                }
            ),
            "publication_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "authors": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter author names in publication order",
                    "rows": 3,
                    "autocomplete": "off",
                }
            ),
            "journal": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter journal or publication venue",
                    "autocomplete": "off",
                }
            ),
            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter the publication abstract or research summary",
                    "rows": 6,
                }
            ),
            "keywords": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: machine learning, healthcare, AI",
                    "autocomplete": "off",
                }
            ),
            "publication_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "id": "id_publication_date",
                    "autocomplete": "off",
                    "placeholder": "Select publication date",
                    "type": "date",
                }
            ),
            "publication_status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "doi": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter DOI if available",
                    "autocomplete": "off",
                }
            ),
            "indexed_status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "indexing_database": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "manuscript_file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "acceptance_letter": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                }
            ),
            "supporting_document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png",
                }
            ),
            "student_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Add any additional notes or remarks",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        self.phd_student = kwargs.pop(
            "phd_student",
            None,
        )

        self.completed_milestones = kwargs.pop(
            "completed_milestones",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.phd_student is None:
            raise ValueError("ResearchPublicationForm requires a PhD student instance.")

        self.fields["milestone"].label = "Related Research Milestone"
        self.fields["title"].label = "Publication Title"
        self.fields["publication_type"].label = "Publication Type"
        self.fields["authors"].label = "Authors"
        self.fields["journal"].label = "Journal / Publication Venue"
        self.fields["abstract"].label = "Abstract / Research Summary"
        self.fields["keywords"].label = "Keywords"
        self.fields["publication_date"].label = "Publication Date"
        self.fields["publication_status"].label = "Publication Status"
        self.fields["doi"].label = "DOI"
        self.fields["indexed_status"].label = "Indexing Status"
        self.fields["indexing_database"].label = "Indexing Database"
        self.fields["manuscript_file"].label = "Published Paper / Manuscript"
        self.fields["acceptance_letter"].label = "Acceptance Letter"
        self.fields["supporting_document"].label = "Supporting Document"
        self.fields["student_remarks"].label = "Additional Remarks"

        self.fields["milestone"].required = False
        self.fields["authors"].required = False
        self.fields["journal"].required = False
        self.fields["abstract"].required = False
        self.fields["keywords"].required = False
        self.fields["doi"].required = False
        self.fields["manuscript_file"].required = False
        self.fields["acceptance_letter"].required = False
        self.fields["supporting_document"].required = False
        self.fields["student_remarks"].required = False

        self.fields["publication_type"].required = True
        self.fields["publication_date"].required = True
        self.fields["publication_status"].required = True
        self.fields["indexed_status"].required = True
        self.fields["indexing_database"].required = True

        if self.completed_milestones is not None:
            milestone_queryset = self.completed_milestones.filter(
                phd_student=self.phd_student,
                status="COMPLETED",
            )
        else:
            milestone_queryset = ResearchMilestone.objects.filter(
                phd_student=self.phd_student,
                status="COMPLETED",
            )

        used_milestone_ids = (
            ResearchPublication.objects.filter(
                phd_student=self.phd_student,
                milestone__isnull=False,
            )
            .exclude(
                pk=self.instance.pk if self.instance and self.instance.pk else None,
            )
            .values_list(
                "milestone_id",
                flat=True,
            )
        )

        self.fields["milestone"].queryset = milestone_queryset.exclude(
            milestone_id__in=used_milestone_ids,
        ).order_by(
            "-sequence_number",
        )

        self.fields["milestone"].empty_label = "No Specific Milestone"

    def clean_title(self):

        title = self.cleaned_data.get(
            "title",
        )

        if not title:
            raise forms.ValidationError("Please enter the publication title.")

        title = title.strip()

        if len(title) < 5:
            raise forms.ValidationError(
                "Publication title must contain at least 5 characters."
            )

        if len(title) > 255:
            raise forms.ValidationError(
                "Publication title cannot exceed 255 characters."
            )

        return title

    def clean_authors(self):

        authors = self.cleaned_data.get(
            "authors",
        )

        if not authors:
            return authors

        authors = authors.strip()

        if len(authors) > 5000:
            raise forms.ValidationError(
                "Author information cannot exceed 5000 characters."
            )

        return authors

    def clean_journal(self):

        journal = self.cleaned_data.get(
            "journal",
        )

        if not journal:
            return journal

        journal = journal.strip()

        if len(journal) < 2:
            raise forms.ValidationError(
                "Journal or publication venue must contain at least 2 characters."
            )

        if len(journal) > 255:
            raise forms.ValidationError(
                "Journal or publication venue cannot exceed 255 characters."
            )

        return journal

    def clean_abstract(self):

        abstract = self.cleaned_data.get(
            "abstract",
        )

        if not abstract:
            return abstract

        abstract = abstract.strip()

        if len(abstract) > 10000:
            raise forms.ValidationError("Abstract cannot exceed 10000 characters.")

        return abstract

    def clean_keywords(self):

        keywords = self.cleaned_data.get(
            "keywords",
        )

        if not keywords:
            return keywords

        keywords = keywords.strip()

        if len(keywords) > 500:
            raise forms.ValidationError("Keywords cannot exceed 500 characters.")

        return keywords

    def clean_publication_date(self):

        publication_date = self.cleaned_data.get(
            "publication_date",
        )

        if not publication_date:
            raise forms.ValidationError("Please select the publication date.")

        if publication_date > timezone.now().date():
            raise forms.ValidationError("Publication date cannot be in the future.")

        return publication_date

    def clean_doi(self):

        doi = self.cleaned_data.get(
            "doi",
        )

        if not doi:
            return doi

        doi = doi.strip()

        if len(doi) > 255:
            raise forms.ValidationError("DOI cannot exceed 255 characters.")

        return doi

    def clean_student_remarks(self):

        remarks = self.cleaned_data.get(
            "student_remarks",
        )

        if not remarks:
            return remarks

        remarks = remarks.strip()

        if len(remarks) > 5000:
            raise forms.ValidationError("Remarks cannot exceed 5000 characters.")

        return remarks

    def clean_milestone(self):

        milestone = self.cleaned_data.get(
            "milestone",
        )

        if not milestone:
            return milestone

        if milestone.phd_student_id != self.phd_student.phd_student_id:
            raise forms.ValidationError(
                "The selected research milestone does not belong to you."
            )

        if milestone.status != "COMPLETED":
            raise forms.ValidationError(
                "A publication can only be linked to a completed research milestone."
            )

        existing_publication = (
            ResearchPublication.objects.filter(
                phd_student=self.phd_student,
                milestone=milestone,
            )
            .exclude(
                pk=self.instance.pk if self.instance and self.instance.pk else None,
            )
            .first()
        )

        if existing_publication:
            raise forms.ValidationError(
                "This research milestone is already linked to another publication."
            )

        return milestone

    def clean(self):

        cleaned_data = super().clean()

        if self.errors:
            return cleaned_data

        completed_milestone_exists = ResearchMilestone.objects.filter(
            phd_student=self.phd_student,
            status="COMPLETED",
        ).exists()

        if not completed_milestone_exists:
            raise forms.ValidationError(
                (
                    "You must complete at least one research milestone "
                    "before adding a publication."
                )
            )

        milestone = cleaned_data.get(
            "milestone",
        )

        if milestone:

            if milestone.status != "COMPLETED":
                self.add_error(
                    "milestone",
                    (
                        "Only completed research milestones can be "
                        "associated with a publication."
                    ),
                )

            existing_publication = (
                ResearchPublication.objects.filter(
                    phd_student=self.phd_student,
                    milestone=milestone,
                )
                .exclude(
                    pk=self.instance.pk if self.instance and self.instance.pk else None,
                )
                .exists()
            )

            if existing_publication:
                self.add_error(
                    "milestone",
                    "This research milestone has already been used for another publication.",
                )

        return cleaned_data

    def save(self, commit=True):

        publication = super().save(
            commit=False,
        )

        publication.phd_student = self.phd_student

        if commit:
            publication.save()

        return publication


class FinalDissertationSubmissionForm(forms.ModelForm):

    class Meta:
        model = FinalDissertationSubmission

        fields = [
            "dissertation_title",
            "abstract",
            "dissertation_file",
            "student_remarks",
        ]

        widgets = {
            "dissertation_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": "255",
                    "placeholder": "Enter your final dissertation title",
                    "autocomplete": "off",
                }
            ),
            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "maxlength": "20000",
                    "placeholder": "Enter the abstract of your final dissertation.",
                }
            ),
            "dissertation_file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "student_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "maxlength": "5000",
                    "placeholder": "Add any additional remarks for your advisor or review committee.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["dissertation_title"].required = True
        self.fields["abstract"].required = True
        self.fields["dissertation_file"].required = True
        self.fields["student_remarks"].required = False

    def clean_dissertation_title(self):
        title = self.cleaned_data.get("dissertation_title")

        if not title:
            raise forms.ValidationError("Please enter the final dissertation title.")

        title = title.strip()

        if len(title) < 5:
            raise forms.ValidationError(
                "Dissertation title must contain at least 5 characters."
            )

        if len(title) > 255:
            raise forms.ValidationError(
                "Dissertation title cannot exceed 255 characters."
            )

        return title

    def clean_abstract(self):
        abstract = self.cleaned_data.get("abstract")

        if not abstract:
            raise forms.ValidationError("Please enter the dissertation abstract.")

        abstract = abstract.strip()

        if len(abstract) < 50:
            raise forms.ValidationError("Abstract must contain at least 50 characters.")

        if len(abstract) > 20000:
            raise forms.ValidationError("Abstract cannot exceed 20,000 characters.")

        return abstract

    def clean_dissertation_file(self):
        dissertation_file = self.cleaned_data.get("dissertation_file")

        if not dissertation_file:
            raise forms.ValidationError(
                "Please upload your final dissertation document."
            )

        allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
        }

        file_name = dissertation_file.name.lower()

        if "." not in file_name:
            raise forms.ValidationError("Please upload a valid dissertation document.")

        extension = file_name[file_name.rfind(".") :]

        if extension not in allowed_extensions:
            raise forms.ValidationError("Only PDF, DOC, and DOCX files are allowed.")

        max_size = 100 * 1024 * 1024

        if dissertation_file.size <= 0:
            raise forms.ValidationError("The uploaded dissertation file is empty.")

        if dissertation_file.size > max_size:
            raise forms.ValidationError("Dissertation file cannot exceed 100 MB.")

        return dissertation_file

    def clean_student_remarks(self):
        remarks = self.cleaned_data.get("student_remarks")

        if not remarks:
            return ""

        remarks = remarks.strip()

        if len(remarks) > 5000:
            raise forms.ValidationError(
                "Student remarks cannot exceed 5,000 characters."
            )

        return remarks

    def clean(self):
        cleaned_data = super().clean()

        title = cleaned_data.get("dissertation_title")
        abstract = cleaned_data.get("abstract")
        remarks = cleaned_data.get("student_remarks")

        if title:
            cleaned_data["dissertation_title"] = title.strip()

        if abstract:
            cleaned_data["abstract"] = abstract.strip()

        if remarks:
            cleaned_data["student_remarks"] = remarks.strip()

        return cleaned_data

from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from Students.Leo_Student.models import DissertationDefense


class DissertationDefenseScheduleForm(forms.ModelForm):

    class Meta:
        model = DissertationDefense
        fields = [
            "defense_date",
            "defense_time",
            "location",
        ]

        widgets = {
            "defense_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "defense_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "type": "text",
                    "class": "form-control",
                    "placeholder": "Select defense location",
                    "autocomplete": "off",
                }
            ),
        }

        labels = {
            "defense_date": "Defense Date",
            "defense_time": "Defense Time",
            "location": "Location",
        }

    def clean_defense_date(self):
        defense_date = self.cleaned_data.get("defense_date")

        if defense_date and defense_date < timezone.localdate():
            raise ValidationError(
                "Defense date cannot be in the past."
            )

        return defense_date

    def clean(self):
        cleaned_data = super().clean()

        defense_date = cleaned_data.get("defense_date")
        defense_time = cleaned_data.get("defense_time")

        if defense_date and defense_time:
            defense_datetime = timezone.make_aware(
                datetime.combine(
                    defense_date,
                    defense_time,
                )
            )

            if defense_datetime <= timezone.now():
                raise ValidationError(
                    "Defense date and time must be in the future."
                )

        return cleaned_data

        