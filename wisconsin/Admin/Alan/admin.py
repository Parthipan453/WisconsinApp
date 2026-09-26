from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category,
    Tag,
    Article,
    ArticleBlock,
    RelatedArticle,
    ArticleBlockMedia,
)
admin.site.register(Article)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(RelatedArticle)
admin.site.register(ArticleBlockMedia)
admin.site.register(ArticleBlock)
