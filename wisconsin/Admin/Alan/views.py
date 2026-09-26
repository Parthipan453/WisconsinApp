from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import json
from .models import Category, Article
from .forms import CategoryForm

from .services.article_service import save_article
from .services.tag_service import save_tags
from .services.block_service import save_blocks
from .services.block_media_service import save_block_media
from .services.related_service import save_related_article
from django.template.loader import render_to_string
from django.core.paginator import Paginator

def admin_news(request):

    published_news = (
        Article.objects.filter(status="published")
        .select_related("category")
        .order_by("-published_at")
    )
    paginator = Paginator(published_news, 2)
    published_news = paginator.get_page(1)
    total_news = Article.objects.count()
    pub_count = Article.objects.filter(status="published").count()
    draft_count = Article.objects.filter(status="draft").count()
    removed_count = Article.objects.filter(status="removed").count()

    drafted_news = (
        Article.objects.filter(status="draft")
        .select_related("category")
        .order_by("created_at")
    )
    removed_news = Article.objects.filter(status="removed")
    context = {
        "published_news": published_news,
        "drafted_news": drafted_news,
        "total_news": total_news,
        "pub_count": pub_count,
        "draft_count": draft_count,
        "removed_count": removed_count,
        "removed_news": removed_news,
        "categories": Category.objects.all().order_by("category_name"),
    }

    return render(request, "admin_news.html", context)


# NEWS REMOVE FUNCTION


@require_POST
def remove_news(request, article_id):

    try:
        article = Article.objects.get(id=article_id)

        article.status = "removed"
        article.save(update_fields=["status"])

        return JsonResponse(
            {"success": True, "message": "News moved to bin successfully."}
        )

    except Article.DoesNotExist:

        return JsonResponse(
            {"success": False, "message": "News not Found."}, status=404
        )
@require_POST
def publish_news(request, article_id):

    try:
        article = Article.objects.get(id=article_id)

        article.status = "published"
        article.save(update_fields=["status"])

        return JsonResponse({
            "success": True,
            "message": "News published successfully."
        })

    except Article.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "News not found."
        }, status=404)

def news_editor(request, article_id=None):

    categories = list(Category.objects.values("category_name"))

    article = None

    if article_id:
        article = get_object_or_404(Article, id=article_id)

    context = {
        "categories_json": json.dumps(categories),
        "article": article,
        "is_edit": article is not None,
        "article_json": None,
    }

    if article:

        blocks = []

        for block in (
            article.blocks.all().prefetch_related("media_files").order_by("order")
        ):

            block_data = block.data.copy() if block.data else {}
            
            if block.block_type == "gallery":
                block_data.setdefault("images", [])

            block_data["id"] = block.id
            block_data["type"] = block.block_type

            media_files = list(block.media_files.all())

            if block.block_type in ["image", "video"]:

                if media_files:
                    block_data["existingFile"] = media_files[0].file.url
                    block_data["fileName"] = media_files[0].file.name.split("/")[-1]
                    
            elif block.block_type == "gallery":

                gallery = [
                    {
                        "url": media.file.url,
                        "name": media.file.name.split("/")[-1],
                    }
                    for media in media_files
                ]

                block_data["existingGallery"] = gallery
                block_data["images"] = gallery

            blocks.append(block_data)
            
            

        context["article_json"] = json.dumps(
            {
                "title": article.title,
                "subtitle": article.subtitle,
                "category": article.category.category_name,
                "readingTime": article.reading_time,
                "authorName": article.author_name,
                "authorRole": article.author_role,
                "authorBio": article.author_bio,
                "authorAvatar": (
                    article.author_avatar.url if article.author_avatar else ""
                ),
                "authorAvatarName": (
                    article.author_avatar.name.split("/")[-1]
                    if article.author_avatar
                    else ""
                ),
                "socialTwitter": article.author_twitter,
                "socialLinkedin": article.author_linkedin,
                "socialWebsite": article.author_website,
                "heroCaption": article.hero_caption,
                "heroMedia": article.hero_media.url if article.hero_media else "",
                "heroFileName": (
                    article.hero_media.name.split("/")[-1] if article.hero_media else ""
                ),
                "tags": list(article.tags.values_list("tag_name", flat=True)),
                "blocks": blocks,
            }
        )

    return render(request, "news_editor.html", context)


# GET ARTICLE DATA FOR EDITING


def get_article_data(request, article_id):

    article = get_object_or_404(Article, id - article_id)
    data = {
        "title": article.title,
        "subtitle": article.subtitle or "",
        "category": article.category.category_name if article.category else "",
        "reading_time": article.reading_time,
        "author_name": article.author_name or "",
        "author_role": article.author_role or "",
        "author_bio": article.author_bio or "",
        "author_avatar": article.author_avatar.url if article.author_avatar else "",
        "author_twitter": article.author_twitter or "",
        "author_linkedin": article.author_linkedin or "",
        "author_website": article.author_website or "",
        "hero_caption": article.hero_caption or "",
        "hero_media": article.hero_media.url if article.hero_media else "",
        "status": article.status,
    }

    return JsonResponse(data)


def template_view(request):
    return render(request, "template_view.html")


@require_POST
@transaction.atomic
def create_article(request):

    print("1. CREATE ARTICLE")

    try:
        print("2. BEFORE save_article")

        article = save_article(request)

        print("3. AFTER save_article", article.id)

        save_tags(article, request)
        print("4. AFTER save_tags")

        save_blocks(article, request)
        print("5. AFTER save_blocks")

        save_block_media(article, request)
        print("6. AFTER save_block_media")

        save_related_article(article, request)
        print("7. AFTER save_related_article")

        return JsonResponse({
            "success": True,
            "message": "Article saved successfully.",
            "article_id": article.id,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": str(e)}, status=400)


# ADD CATEGORY VIEWS


def add_category(request):

    print("POST DATA:", request.POST)

    form = CategoryForm(request.POST)

    if form.is_valid():

        category = form.save()

        return JsonResponse(
            {
                "success": True,
                "category": {
                    "id": category.id,
                    "category_name": category.category_name,
                },
            }
        )

    return JsonResponse(
        {"success": False, "errors": form.errors.get_json_data()}, status=400
    )


# EDIT ARTICLE FUNCTION


@require_POST
@transaction.atomic
def update_article(request, article_id):

    try:

        article = get_object_or_404(Article, id=article_id)

        article.title = request.POST.get("title", "").strip()

        article.subtitle = request.POST.get("subtitle", "").strip()

        category_name = request.POST.get("category")

        article.category = Category.objects.get(category_name=category_name)

        article.reading_time = request.POST.get("reading_time") or 0

        article.author_name = request.POST.get("author_name", "").strip()

        article.author_role = request.POST.get("author_role", "").strip()

        article.author_bio = request.POST.get("author_bio", "").strip()

        article.author_twitter = request.POST.get("author_twitter", "").strip()

        article.author_linkedin = request.POST.get("author_linkedin", "").strip()

        article.author_website = request.POST.get("author_website", "").strip()

        article.hero_caption = request.POST.get("hero_caption", "").strip()

        article.status = request.POST.get("status", article.status)

        if request.FILES.get("hero_media"):
            article.hero_media = request.FILES["hero_media"]

        if request.FILES.get("author_avatar"):
            article.author_avatar = request.FILES["author_avatar"]

        article.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Article updated successfully.",
                "article_id": article.id,
            }
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        return JsonResponse({"success": False, "message": str(e)}, status=400)


# FILTERS

def filter_news(request):

    status = request.GET.get("status", "published")
    category = request.GET.get("category")
    date = request.GET.get("date")
    page = request.GET.get("page")

    news = Article.objects.filter(status=status)

    if category:
        news = news.filter(category_id=category)

    if date:
        news = news.filter(created_at__date=date)

    paginator = Paginator(news, 2)

    published_news = paginator.get_page(page)

    html = render_to_string(
        "partials/news_list.html",
        {
            "published_news": published_news,
        },
        request=request,
    )

    return JsonResponse({
        "success": True,
        "html": html,
    })
    
    
##################################### HOSPITAL VIEWS START ###########################################


def hospital_dashboard(request):
    return render(request, "alan/hospital_dashboard.html")


def create_hospital(request):
    return render(request,"alan/create_hospital.html")