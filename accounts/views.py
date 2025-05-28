from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .models import UserProfile
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import re

@csrf_protect
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, '两次输入的密码不一致')
            return render(request, 'account/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return render(request, 'account/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, '该邮箱已被注册')
            return render(request, 'account/signup.html')
        
        try:
            # 创建用户
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            # 使用 authenticate 获取带有后端的用户对象
            authenticated_user = authenticate(
                request,
                username=username,
                password=password1
            )
            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, '注册成功！')
                return redirect('/')
            else:
                messages.error(request, '注册成功但登录失败，请手动登录')
                return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f'注册失败：{str(e)}')
            return render(request, 'account/signup.html')
    
    return render(request, 'account/signup.html')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 尝试使用用户名登录
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            # 如果用户名登录失败，尝试使用邮箱登录
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            login(request, user)
            messages.success(request, '登录成功！')
            return redirect('/')
        else:
            messages.error(request, '用户名/邮箱或密码错误')
            return render(request, 'account/login.html')
    
    return render(request, 'account/login.html')

def custom_logout(request):
    logout(request)
    messages.success(request, '已成功退出登录')
    return redirect('/')

@csrf_protect
def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # 生成密码重置令牌
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # 发送密码重置邮件
            subject = '重置您的密码'
            message = render_to_string('account/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
            try:
                send_mail(subject, message, None, [email])
                messages.success(request, '密码重置链接已发送到您的邮箱')
            except Exception as e:
                messages.error(request, '发送邮件失败，请稍后重试')
        except User.DoesNotExist:
            # 为了安全，即使用户不存在也显示成功消息
            messages.success(request, '如果该邮箱存在，密码重置链接已发送')
        return redirect('accounts:login')
    return render(request, 'account/password_reset.html')

@csrf_protect
def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 != password2:
                messages.error(request, '两次输入的密码不一致')
            else:
                user.set_password(password1)
                user.save()
                messages.success(request, '密码已成功重置，请使用新密码登录')
                return redirect('accounts:login')
        return render(request, 'account/password_reset_confirm.html')
    else:
        messages.error(request, '密码重置链接无效或已过期')
        return redirect('accounts:login')

@login_required
def profile_view(request):
    """查看个人资料"""
    user_profile = request.user.profile
    return render(request, 'account/profile.html', {
        'profile': user_profile
    })

def is_valid_url(url):
    """验证URL格式"""
    if not url:  # 如果是空值，直接返回True
        return True
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

@login_required
def profile_edit(request):
    """编辑个人资料"""
    user_profile = request.user.profile
    
    if request.method == 'POST':
        # 基本信息
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')  # 邮箱是必填项
        user.save()
        
        # 个人资料
        user_profile.bio = request.POST.get('bio', '') or None
        user_profile.birth_date = request.POST.get('birth_date') or None
        user_profile.gender = request.POST.get('gender', '') or None
        user_profile.phone = request.POST.get('phone', '') or None
        user_profile.address = request.POST.get('address', '') or None
        user_profile.education = request.POST.get('education', '') or None
        user_profile.occupation = request.POST.get('occupation', '') or None
        user_profile.company = request.POST.get('company', '') or None
        
        # 处理URL字段，确保空字符串转换为None，并验证URL格式
        website = request.POST.get('website', '').strip()
        social_github = request.POST.get('social_github', '').strip()
        social_weibo = request.POST.get('social_weibo', '').strip()
        
        # 验证URL格式
        if website and not is_valid_url(website):
            messages.error(request, '个人网站地址格式无效，请输入完整的URL（包含http://或https://）')
            return render(request, 'account/profile_edit.html', {'profile': user_profile})
        if social_github and not is_valid_url(social_github):
            messages.error(request, 'GitHub地址格式无效，请输入完整的URL（包含http://或https://）')
            return render(request, 'account/profile_edit.html', {'profile': user_profile})
        if social_weibo and not is_valid_url(social_weibo):
            messages.error(request, '微博地址格式无效，请输入完整的URL（包含http://或https://）')
            return render(request, 'account/profile_edit.html', {'profile': user_profile})
            
        user_profile.website = website or None
        user_profile.social_github = social_github or None
        user_profile.social_weibo = social_weibo or None
        user_profile.social_wechat = request.POST.get('social_wechat', '') or None
        user_profile.interests = request.POST.get('interests', '') or None
        
        # 处理头像上传
        if 'avatar' in request.FILES:
            user_profile.avatar = request.FILES['avatar']
        
        user_profile.save()
        messages.success(request, '个人资料更新成功！')
        return redirect('accounts:profile')
        
    return render(request, 'account/profile_edit.html', {
        'profile': user_profile
    })

@login_required
def avatar_upload(request):
    """上传头像的AJAX处理"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            user_profile = request.user.profile
            user_profile.avatar = request.FILES['avatar']
            user_profile.save()
            return JsonResponse({
                'success': True,
                'avatar_url': user_profile.get_avatar_url()
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': '无效的请求'})
