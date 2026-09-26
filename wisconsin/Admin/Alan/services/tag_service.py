from ..models import Tag
import json
def save_tags(article, request):
  
  tags_json = request.POST.get("tags", "[]")
  
  try:
    tags = json.loads(tags_json)
  except json.JSONDecodeError:
    tags = []
  
  # Remove existing tags
  
  article.tags.clear()
  
  for tag_name in tags:
    
    tag_name = tag_name.strip()
    
    if not tag_name:
      continue
    
    tag, created = Tag.objects.get_or_create(
      tag_name=tag_name
    )
    article.tags.add(tag)
  return article.tags.all()