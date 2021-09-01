from django.db import models

# Create your models here.

class User(models.Model):

    gender = (
        ('male', '男'),
        ('female', '女'),
    )

    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    sex = models.CharField(max_length=32, choices=gender, default='男')
    c_time = models.DateTimeField(auto_now_add=True)
    has_confirmed = models.BooleanField(default=False)

    def __str__(self):  #使用__str__方法帮助人性化显示对象信息
        return self.username

    class Meta: #元数据里定义用户按创建时间的反序排列，也就是最近的最先显示
        ordering = ["-c_time"]
        verbose_name = "用户"
        verbose_name_plural = "用户"

class ConfirmString(models.Model):
    code = models.CharField(max_length=256)     #code字段是哈希后的注册码
    user = models.OneToOneField('User', on_delete=models.CASCADE)   #user是关联的一对一用户
    c_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + ":  " + self.code

    class Meta:
        ordering = ["-c_time"]
        verbose_name = "确认码"
        verbose_name_plural = "确认码"

