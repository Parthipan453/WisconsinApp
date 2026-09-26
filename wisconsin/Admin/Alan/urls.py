from django.urls import path
from .import views
urlpatterns = [
    path("admin_news/",views.admin_news,name="admin_news"),
    path("news_editor/",views.news_editor,name="news_editor"),
    path("article/create/",views.create_article,name="create_article"),
    path("preview_page/",views.template_view,name="preview_page"),
    path("add_category/",views.add_category,name="add_category"),
    path("news_editor/<int:article_id>/",views.news_editor,name="edit_news"),
    path("article/<int:article_id>/data/",views.get_article_data,name="get_article_data"),
    path("article/<int:article_id>/update/",views.update_article,name="update_article"),
    path("remove_news/<int:article_id>/",views.remove_news,name="remove_news"),
    path("publish-news/<int:article_id>/",views.publish_news,name="publish_news"),
    path("news/filter/",views.filter_news,name="filter_news"),
    
    ############# HOSPITAL VIEWS START ########################
]
