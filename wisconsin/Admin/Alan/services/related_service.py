from ..models import Article, RelatedArticle

def save_related_article(article, request):
  
  related_ids = request.POST.getlist("related_article")
  
  if not related_ids:
    return
  
  for related_id in related_ids:
    
    try:
      
      related_article = Article.objects.get(id=related_id)
      
      if related_article.id != article.id:
        
        RelatedArticle.objects.get_or_create(article=article, related_article=related_article)
    
    except Article.DoesNotExist:
      continue