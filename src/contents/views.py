import datetime

from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from contents.models import Content, Author, Tag, ContentTag
from contents.serializers import ContentSerializer, ContentPostSerializer


class ContentAPIView(APIView):

    def get(self, request):
        """
        TODO: Client is complaining about the app performance, the app is loading very slowly, our QA identified that
         this api is slow af. Make the api performant. Need to add pagination. But cannot use rest framework view set.
         As frontend, app team already using this api, do not change the api schema.
         Need to send some additional data as well,
         --------------------------------
         1. Total Engagement = like_count + comment_count + share_count
         2. Engagement Rate = Total Engagement / Views
         Users are complaining these additional data is wrong.
         Need filter support for client side. Add filters for (author_id, author_username, timeframe )
         For timeframe, the content's timestamp must be withing 'x' days.
         Example: api_url?timeframe=7, will get contents that has timestamp now - '7' days
         --------------------------------
         So things to do:
         1. Make the api performant
         2. Fix the additional data point in the schema
            - Total Engagement = like_count + comment_count + share_count
            - Engagement Rate = Total Engagement / Views
            - Tags: List of tags connected with the content
         3. Filter Support for client side
            - author_id: Author's db id
            - author_username: Author's username
            - timeframe: Content that has timestamp: now - 'x' days
            - tag_id: Tag ID
            - title (insensitive match IE: SQL `ilike %text%`)
         4. Must not change the inner api schema
         5. Remove metadata and secret value from schema
         6. Add pagination
            - Should have page number pagination
            - Should have items per page support in query params
            Example: `api_url?items_per_page=10&page=2`
        """
        query_params = request.query_params
        author_id = query_params.get("author_id")
        author_username = query_params.get("author_username")
        timeframe = query_params.get("timeframe")
        tag_name = query_params.get("tag")
        title = query_params.get("title")
        items_per_page = int(query_params.get("items_per_page", 100))
        page = int(query_params.get("page", 1))

        queryset = Content.objects.all()

        # Apply filters
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if author_username:
            queryset = queryset.filter(author__username__iexact=author_username)
        if timeframe:
            timeframe_date = datetime.date.today() - datetime.timedelta(days=int(timeframe))
            queryset = queryset.filter(timestamp__gte=timeframe_date)
        if tag_name:
            queryset = queryset.filter(contenttag__tag__name__iexact=tag_name)
        if title:
            queryset = queryset.filter(title__icontains=title)

        # Pagination
        start = items_per_page * (page - 1)
        end = start + items_per_page
        queryset = queryset.order_by("-id")[start:end]

        data_list = []
        for query in queryset:
            author = query.author
            data = {
                "content": query,
                "author": author
            }
            data_list.append(data)

        serialized = ContentSerializer(data_list, many=True)
        for serialized_data in serialized.data:
            # Calculating `Total Engagement`
            # Calculating `Engagement Rate`
            like_count = serialized_data.get("like_count", 0)
            comment_count = serialized_data.get("comment_count", 0)
            share_count = serialized_data.get("share_count", 0)
            view_count = serialized_data.get("view_count", 0)
            total_engagement = like_count + comment_count + share_count
            if view_count > 0:
                engagement_rate = total_engagement / view_count
            else:
                engagement_rate = 0
            serialized_data["content"]["engagement_rate"] = engagement_rate
            serialized_data["content"]["total_engagement"] = total_engagement
            tags = list(
                ContentTag.objects.filter(
                    content_id=serialized_data["content"]["id"]
                ).values_list("tag__name", flat=True)
            )
            serialized_data["content"]["tags"] = tags
        return Response(serialized.data, status=status.HTTP_200_OK)

    def post(self, request, ):
        """
        TODO: This api is very hard to read, and inefficient.
         The users complaining that the contents they are seeing is not being updated.
         Please find out, why the stats are not being updated.
         ------------------
         Things to change:
         1. This api is hard to read, not developer friendly
         2. Support list, make this api accept list of objects and save it
         3. Fix the users complain
        """

        serializer = ContentPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        response_data = []

        author = validated_data.get("author")
        hashtags = validated_data.get("hashtags")

        author_object = self.get_or_create_author(author)

        content = validated_data
        content['author'] = author_object
        content_object = self.get_or_create_content(content)

        self.update_content_tags(content_object, hashtags)

        response_data.append(ContentSerializer({"content": content_object, "author": author_object}).data)

        return Response(response_data, status=status.HTTP_200_OK)

    def get_or_create_author(self, author_data):
        author, _ = Author.objects.get_or_create(
            unique_id=author_data["unique_external_id"],
            defaults={
                "username": author_data["unique_name"],
                "name": author_data["full_name"],
                "url": author_data["url"],
                "title": author_data["title"],
                "big_metadata": author_data.get("big_metadata"),
                "secret_value": author_data.get("secret_value"),
            }
        )
        return author

    def get_or_create_content(self, content_data):
        content, _ = Content.objects.get_or_create(
            unique_id=content_data["unq_external_id"],
            defaults={
                "author": content_data["author"],
                "title": content_data.get("title"),
                "big_metadata": content_data.get("big_metadata"),
                "secret_value": content_data.get("secret_value"),
                "thumbnail_url": content_data.get("thumbnail_view_url"),
                "like_count": content_data["stats"]["likes"],
                "comment_count": content_data["stats"]["comments"],
                "share_count": content_data["stats"]["shares"],
                "view_count": content_data["stats"]["views"],
            }
        )
        return content

    def update_content_tags(self, content, hashtags):
        # Clear existing tags
        ContentTag.objects.filter(content=content).delete()

        for tag_name in hashtags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            ContentTag.objects.create(tag=tag, content=content)


class ContentStatsAPIView(APIView):
    """
    TODO: This api is taking way too much time to resolve.
     Contents that will be fetched using `ContentAPIView`, we need stats for that
     So it must have the same filters as `ContentAPIView`
     Filter Support for client side
            - author_id: Author's db id
            - author_username: Author's username
            - timeframe: Content that has timestamp: now - 'x' days
            - tag_id: Tag ID
            - title (insensitive match IE: SQL `ilike %text%`)
     -------------------------
     Things To do:
     1. Make the api performant
     2. Fix the additional data point (IE: total engagement, total engagement rate)
     3. Filter Support for client side
         - author_id: Author's db id
         - author_id: Author's db id
         - author_username: Author's username
         - timeframe: Content that has timestamp: now - 'x' days
         - tag_id: Tag ID
         - title (insensitive match IE: SQL `ilike %text%`)
     --------------------------
     Bonus: What changes do we need if we want timezone support?
    """
    def get(self, request):
        query_params = request.query_params

        # Define filters
        author_id = query_params.get("author_id")
        author_username = query_params.get("author_username")
        timeframe = query_params.get("timeframe")
        tag = query_params.get("tag")
        title = query_params.get("title")

        queryset = Content.objects.all()

        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if author_username:
            queryset = queryset.filter(author__username__iexact=author_username)
        if timeframe:
            timeframe_date = timezone.now() - datetime.timedelta(days=int(timeframe))
            queryset = queryset.filter(timestamp__gte=timeframe_date)
        if tag:
            queryset = queryset.filter(contenttag__tag__name__iexact=tag)
        if title:
            queryset = queryset.filter(title__icontains=title)

        stats = queryset.aggregate(
            total_likes=Sum('like_count'),
            total_shares=Sum('share_count'),
            total_views=Sum('view_count'),
            total_comments=Sum('comment_count'),
            total_contents=Count('id'),
            total_followers=Sum('author__followers')
        )

        total_engagement = stats['total_likes'] + stats['total_shares'] + stats['total_comments']
        total_engagement_rate = total_engagement / stats['total_views'] if stats['total_views'] else 0

        data = {
            "total_likes": stats['total_likes'] or 0,
            "total_shares": stats['total_shares'] or 0,
            "total_views": stats['total_views'] or 0,
            "total_comments": stats['total_comments'] or 0,
            "total_engagement": total_engagement or 0,
            "total_engagement_rate": round(total_engagement_rate, 2),
            "total_contents": stats['total_contents'] or 0,
            "total_followers": stats['total_followers'] or 0,
        }

        return Response(data, status=status.HTTP_201_CREATED)
