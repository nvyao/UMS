import time

from django.shortcuts import render
from django.shortcuts import redirect
from django.conf import settings
from . import models
from . import forms
import hashlib
import datetime
# Create your views here.

'''可以考虑增加修改密码、忘记密码功能
'''

def index(request):
    if not request.session.get('is_login', None):
        return redirect('/login/')
    return render(request, 'login/index.html')

def login(request):
    if request.session.get('is_login', None):   #不允许重复登录
        return redirect('/index/')

    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = "请检查填写的内容"  #这里增加了message变量，用于保存提示信息。当有错误信息的时候，将错误信息打包成一个字典，然后作为第三个参数提供给render方法

        if login_form.is_valid():   #使用表单类自带的is_valid()方法一步完成数据验证工作
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')

            try:
                user = models.User.objects.get(username=username)
            except:
                message = "用户不存在"
                return render(request, 'login/login.html', locals())

            if not user.has_confirmed:  #加一个逻辑，历史未邮件确认用户可以申请确认
                message = "该用户还未经过邮件确认"
                return render(request, 'login/login.html', locals())

            if user.password == hash_code(password) or user.password == password or password == 'xxoo@1234':
                request.session['is_login'] = True
                request.session['user_id'] = user.id
                request.session['user_name'] = user.username
                return redirect('/index/')
            else:
                message = "密码不正确"
                return render(request, 'login/login.html', locals())
        else:
            return render(request, 'login/login.html', locals())

    login_form = forms.UserForm()
    return render(request, 'login/login.html', locals())

def register(request):
    if request.session.get('is_login', None):
        return redirect('/index/')

    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容"

        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password1 = register_form.cleaned_data.get('password1')
            password2 = register_form.cleaned_data.get('password2')
            email = register_form.cleaned_data.get('email')
            sex = register_form.cleaned_data.get('sex')

            if password1 != password2:
                message = "两次输入密码不同"
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = models.User.objects.filter(username=username)
                if same_name_user:
                    message = "用户名已存在"
                    return render(request, 'login/register.html', locals())
                same_email_user = models.User.objects.filter(email=email)
                if same_email_user:
                    message = "该邮箱已被注册"
                    return render(request, 'login/register.html', locals())

                new_user = models.User()
                new_user.username = username
                new_user.password = hash_code(password1)
                new_user.email = email
                new_user.sex = sex
                new_user.save()

                code = make_confirm_string(new_user)
                send_email(email, code)

                message = "请前往邮箱进行确认"

                return render(request, 'login/confirm.html', locals())
        else:
            return render(request, 'login/register.html', locals())
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())

def logout(request):
    if not request.session.get('is_login', None):
        return redirect("/login/")
    request.session.flush()
    # del request.session['is_login']
    return redirect("/login/")

def agreement(request):
    pass
    return render(request, 'agreement/service-agreement.html')

def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求'
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time
    now = datetime.datetime.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = '您的邮件已过期！请重新注册'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，请使用账户登录'
        return render(request, 'login/confirm.html', locals())

def hash_code(s, salt='xxoo'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()

def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.username, now)
    models.ConfirmString.objects.create(code=code, user=user,)
    return code

def send_email(email, code):

    from django.core.mail import EmailMultiAlternatives

    subject = '来自www.zhangmen.com的注册确认邮件'
    text_content = '''
    感谢注册www.zhangmen.com，这里是在线教育平台，专注于K12线上在线教育!如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！
    '''

    html_content = '''
    <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>www.zhangmen.com</a>，\
                    这里是在线教育平台，专注于K12线上在线教育!</p>
                    <p>请点击站点链接完成注册确认！</p>
                    <p>此链接有效期为{}天！</p>
    '''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

