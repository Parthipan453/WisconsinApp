from ..models import ArticleBlock
import json

def save_blocks(article, request):

    blocks_json = request.POST.get("blocks", "[]")

    try:
        blocks = json.loads(blocks_json)
    except json.JSONDecodeError:
        blocks = []
    
    

    for index, block in enumerate(blocks):

        block_type = block.get("type", "")

        title = ""
        content = ""
        caption = ""
        level = "h2"
        
        block_type = block.get("type", "")

        if block_type == "box-highlight":
            block_type = "highlight"
        elif block_type == "box-info":
            block_type = "info"
        elif block_type == "box-warning":
            block_type = "warning"

        if block_type == "heading":
            title = block.get("text", "")
            level = block.get("level", "")
            

        elif block_type == "paragraph":
            content = block.get("content", "")

        elif block_type == "image":
            caption = block.get("caption", "")
        
        elif block_type == "video":
            caption = block.get("caption", "")
            content = block.get("embedUrl", "")

        elif block_type in ["highlight", "info", "warning"]:
            title = block.get("title", "")
            content = block.get("content", "")

        elif block_type == "quote":
            content = block.get("quote", "")
            caption = block.get("author", "")

        elif block_type == "list":
            content = "\n".join(block.get("items", []))

        elif block_type == "table":
            content = json.dumps(block.get("rows", []))

        elif block_type == "cta":
            title = block.get("title", "")
            content = block.get("content", "")

        ArticleBlock.objects.create(
            article=article,
            order=index,
            block_type=block_type,
            title=title,
            level=level,
            content=content,
            caption=caption,
            data=block
        )
        print("===== DB BLOCKS =====")

    for b in article.blocks.all():
        print(
            b.id,
            b.block_type,
            b.content,
            b.caption
        )

    print("=====================")