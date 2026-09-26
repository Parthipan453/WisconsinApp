from django.utils import timezone
from django.shortcuts import get_object_or_404
from ..models import Article,Category


def save_article(request):
  
  status = request.POST.get("status", "draft")
  title = request.POST.get("title", "").strip()
  subtitle = request.POST.get("subtitle", "").strip()
  category_name = request.POST.get("category", "").strip()
  reading_time = request.POST.get("reading_time") or 0
  
  hero_caption = request.POST.get("hero_caption","").strip()
  
  # AUTHOR
  
  author_name = request.POST.get("author_name", "").strip()
  author_role = request.POST.get("author_role", "").strip()
  author_bio = request.POST.get("author_bio", "").strip()
  author_twitter = request.POST.get("author_twitter", "").strip()
  author_linkedin = request.POST.get("author_linkedin", "").strip()
  author_website = request.POST.get("author_website", "").strip()
  
  # FILES
  
  hero_media = request.FILES.get("hero_media")
  author_avatar = request.FILES.get("author_avatar")
  print("=" * 50)
  print(request.FILES)
  print(hero_media)
  print("=" * 50)
  # CATEGORY
  
  category = get_object_or_404(Category, category_name=category_name)
  
  article = Article.objects.create(
    
    title=title,
    subtitle=subtitle,
    category=category,
    reading_time=reading_time,
    hero_media=hero_media,
    hero_caption=hero_caption,
    status=status,
    author_name=author_name,
    author_role=author_role,
    author_bio=author_bio,
    author_avatar=author_avatar,
    author_twitter=author_twitter,
    author_linkedin=author_linkedin,
    author_website=author_website,
    
    
    published_at = timezone.now()
      if status == "published"
      else None
      
    
    
  )
  
  return article