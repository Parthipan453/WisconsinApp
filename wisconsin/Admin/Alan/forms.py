from django import forms
import re
from .models import Article, Category


class ArticleForm(forms.ModelForm):

    class Meta:
        model = Article

        fields = [
            "title",
            "subtitle",
            "category",
            "reading_time",
            "hero_media",
            "hero_caption",
            "author_name",
            "author_role",
            "author_bio",
            "author_avatar",
            "author_twitter",
            "author_linkedin",
            "author_website",
        ]


# CATEGORY VALIDATION


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ["category_name"]

    def clean_category_name(self):

        category_name = self.cleaned_data.get("category_name", "").strip()

        if not category_name:
            raise forms.ValidationError("Category name is required.")

        if len(category_name) > 30:
            raise forms.ValidationError("Category name cannot exceed 30 characters")

        if not re.fullmatch(r"[A-Za-z &]+", category_name):
            raise forms.ValidationError("Only alphabets and spaces are allowed.")

        category_name = " ".join(category_name.split())

        if Category.objects.filter(category_name__iexact=category_name).exists():
            raise forms.ValidationError("Category already exists.")

        return category_name
