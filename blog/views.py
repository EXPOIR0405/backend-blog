from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user if self.request.user.is_authenticated else None)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Comment.objects.all()

    def perform_create(self, serializer):
        try:
            post_id = self.request.data.get('post')
            if not post_id:
                raise ValidationError("post field is required")
            
            post = Post.objects.get(id=post_id)
            serializer.save(author=self.request.user if self.request.user.is_authenticated else None, post=post)
        except Post.DoesNotExist:
            raise ValidationError(f"Post with id {post_id} does not exist")

@api_view(['POST'])
def contact(request):
    try:
        name = request.data.get('name')
        email = request.data.get('email')
        message = request.data.get('message')
        
        logger.info(f"Contact form submitted by {name} ({email})")
        logger.info(f"Using EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        
        if not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
            logger.error("Email settings are not properly configured!")
            return Response({'error': 'Email configuration is missing'}, status=500)

        subject = f'새로운 문의: {name}님으로부터'
        email_message = f"""
        이름: {name}
        이메일: {email}
        
        메시지:
        {message}
        """
        
        try:
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            logger.info("Email sent successfully!")
            return Response({'message': '메시지가 성공적으로 전송되었습니다.'})
        except Exception as mail_error:
            logger.error(f"Failed to send email: {str(mail_error)}")
            return Response({'error': f'Email sending failed: {str(mail_error)}'}, status=500)
            
    except Exception as e:
        logger.error(f"Contact view error: {str(e)}")
        return Response({'error': str(e)}, status=500)
