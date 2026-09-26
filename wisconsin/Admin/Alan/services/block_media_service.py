from ..models import ArticleBlock, ArticleBlockMedia

def save_block_media(article, request):

    blocks = article.blocks.all()

    for index, block in enumerate(blocks):

        uploaded_file = request.FILES.get(f"block_file_{index}")

        if uploaded_file:

            caption = ""

            if isinstance(block.data, dict):
                caption = block.data.get("caption", "")

            ArticleBlockMedia.objects.create(
                block=block,
                file=uploaded_file,
                caption=caption,
                order=0
            )

        gallery_index = 0

        while True:

            gallery_file = request.FILES.get(f"gallery_{index}_{gallery_index}")

            if not gallery_file:
                break

            caption = ""

            if isinstance(block.data, dict):
                caption = block.data.get("caption", "")

            ArticleBlockMedia.objects.create(
                block=block,
                file=gallery_file,
                caption=caption,
                order=gallery_index
            )

            gallery_index += 1

    # 👇 Idhu for loop mudinja apram, function-kulla irukkanum
    print("===== MEDIA SAVED =====")

    for block in article.blocks.all():
        print("BLOCK:", block.id, block.block_type)

        for media in block.media_files.all():
            print("MEDIA:", media.file.name)

    print("=======================")