from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify



# CATEGORY

class Category(models.Model):
  
  category_name = models.CharField(max_length=100,unique=True)
  is_full_crud = models.BooleanField(default=True)
  
  
  def __str__(self):
    return self.category_name


  
# TAG

class Tag(models.Model):
  
  tag_name = models.CharField(max_length=10,unique=True)
  is_full_crud = models.BooleanField(default=True)
  
  def __str__(self):
    return self.tag_name
# ARTICLE

class Article(models.Model):
  
  STATUS = (("draft", "Draft"), ("published", "Published"),("removed", "Removed"))
  
  title = models.CharField(max_length=250)
  subtitle = models.CharField(max_length=300,blank=True)
  slug = models.SlugField(unique=True,blank=True)
  category = models.ForeignKey(Category,on_delete=models.PROTECT,related_name="articles")
  
  reading_time = models.PositiveIntegerField()
  hero_media = models.FileField(upload_to="hero_media/",blank=True,null=True)
  hero_caption = models.CharField(max_length=250,blank=True)
  tags = models.ManyToManyField(Tag,blank=True,related_name="articles")
  status = models.CharField(max_length=20, choices=STATUS, default="draft")
  featured = models.BooleanField(default=False)
  featured_order = models.PositiveIntegerField(blank=True,null=True)
  views = models.PositiveIntegerField(default=0)
  published_at = models.DateTimeField(blank=True,null=True)
  created_at = models.DateTimeField(auto_now=True)
  
  author_name = models.CharField(
    max_length=150,
    blank=True
  )

  author_role = models.CharField(
      max_length=150,
      blank=True
  )

  author_bio = models.TextField(
      blank=True
  )

  author_avatar = models.ImageField(
      upload_to="authors/",
      blank=True,
      null=True
  )

  author_twitter = models.URLField(
      blank=True
  )

  author_linkedin = models.URLField(
      blank=True
  )

  author_website = models.URLField(
      blank=True
  )
  is_full_crud = models.BooleanField(default=True)
  
  def save(self, *args,**kwargs):
    
    if not self.slug:
      
      base_slug = slugify(self.title)
      slug = base_slug
      counter = 1
      
      while Article.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter+= 1
      
      self.slug = slug
    
    super().save(*args, **kwargs)
  
  def __str__(self):
    return self.title
  
  class Meta:
    ordering = ["-published_at", "-created_at"]


class ArticleBlock(models.Model):
  
  BLOCK_TYPES = (
    
    ("heading", "Heading"),
    ("paragraph", "Paragraph"),
    ("image", "Image"),
    ("video", "Video"),
    ("pdf", "PDF"),
    ("quote", "Quote"),
    ("highlight", "Highlight"),
    ("info", "Info"),
    ("warning", "Warning"),
    ("list", "List"),
    ("table", "Table"),
    ("cta", "CTA"),
    ("gallery", "Gallery"),
    ("divider", "Divider")
  )
  
  article = models.ForeignKey(Article,on_delete=models.CASCADE,related_name="blocks")
  order = models.PositiveIntegerField()
  block_type = models.CharField(max_length=20,choices = BLOCK_TYPES)
  title = models.CharField(max_length=250,blank=True)
  content = models.TextField(blank=True)
  caption = models.CharField(max_length=250,blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  level = models.CharField(
        max_length=2,
        blank=True,
        default="h2"
    )
  
  

  data = models.JSONField(
        blank=True,
        null=True
    )

  

  caption = models.CharField(
        max_length=250,
        blank=True
    )
  is_full_crud = models.BooleanField(default=True)
  
  def __str__(self):
    return f"{self.article.title} - {self.block_type}"
  
  class Meta:
    ordering = ["order"]
    
    
    

class ArticleBlockMedia(models.Model):
    block = models.ForeignKey(
        ArticleBlock,
        on_delete=models.CASCADE,
        related_name="media_files"
    )

    file = models.FileField(upload_to="article_blocks/")
    caption = models.CharField(max_length=250, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    is_full_crud = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.block.block_type} - {self.id}"
    
    class Meta:
        ordering = ["order"]



class RelatedArticle(models.Model):
  article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="related_articles"
    )

  related_article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="linked_articles"
    )
  is_full_crud = models.BooleanField(default=True)
  
  def __str__(self):
    return f"{self.article} - {self.related_article}"

  class Meta:
        unique_together = (
            "article",
            "related_article",
        )
