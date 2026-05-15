from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from django.http import HttpResponse

def home_view(request):
    html_content = """
    <html>
        <head>
            <title>Welcome to Microverse 🚀</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: #f9f9f9;
                    color: #333;
                    text-align: center;
                    padding-top: 100px;
                }
                h1 {
                    color: #4CAF50;
                }
                .box {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    display: inline-block;
                }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>👋 Welcome to the Microverse User Service</h1>
                <p>This Django service handles user registration and authentication.</p>
                <p>Start by calling <code>/api/user/register/</code> or <code>/api/user/login/</code>.</p>
            </div>
        </body>
    </html>
    """
    return HttpResponse(html_content)



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, email=email)
        return Response(
            {
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            tokens = get_tokens_for_user(user)
            tokens['user_id'] = user.id
            tokens['username'] = user.username
            return Response(tokens, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
