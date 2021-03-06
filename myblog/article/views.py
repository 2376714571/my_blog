from django.shortcuts import render,HttpResponse,redirect
from .models import ArticlePost
import markdown
from .form import ArticlePostForm
from django.contrib.auth.models import User
from django.db.models import Q
# 引入分页模块
from django.core.paginator import Paginator
from comment.models import Comment
# Create your views here.
def article_list(request):
    search = request.GET.get("search")
    order = request.GET.get("order")
    #用户搜索逻辑
    if search:
        if order == 'total_views':
            # 用 Q对象 进行联合搜索
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            ).order_by('-total_views')
        else:
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            )
    else:
        # 将 search 参数重置为空
        search = ''
        if order == 'total_views':
            article_list = ArticlePost.objects.all().order_by('-total_views')
        else:
            article_list = ArticlePost.objects.all()
    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    # 增加 search 到 context
    context = { 'articles': articles, 'order': order, 'search': search }
    return render(request, 'article/list.html', context)
def article_detail(request,id):
    #取出对应的文章
    article = ArticlePost.objects.get(id=id)
    # 取出文章评论
    comments = Comment.objects.filter(article=id)
    # 浏览量 +1
    article.total_views += 1
    article.save(update_fields=['total_views'])
    # 将markdown语法渲染成html样式
    # 修改 Markdown 语法渲染
    # 修改 Markdown 语法渲染
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
        ]
    )
    article.body = md.convert(article.body)
    #需要传递给模板的对象
    context = {'article':article, 'toc': md.toc, 'comments': comments }
    #载入模板，返回context对象

    return render(request,'article/detail.html',context)
def article_create(request):
    if request.method == 'POST':
        article_post_form = ArticlePostForm(data=request.POST)
        #判断提交的数据是满足模型的要求
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit=False)
            # 指定目前登录的用户为作者
            new_article.author = User.objects.get(id=request.user.id)
            new_article.save()
            return redirect("article:article_list")
        else:
            return HttpResponse("表单内容有误，请重新填写")
    else:
        #创建表单类实例
        article_post_form = ArticlePostForm()
        #赋值上下文
        context = {'article_post_form':article_post_form}
        #返回模板
        return render(request,'article/create.html', context)
#删除文章
def article_safe_delete(request,id):
    # 获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id=id)
    # 过滤非作者的用户
    if request.user != article.author:
        return HttpResponse("抱歉，你无权删除这篇文章。")
    if request.method == 'POST':
        article = ArticlePost.objects.get(id = id)
        article.delete()
        return redirect("article:article_list")
    else:
        return HttpResponse("鬼！")
def article_update(request,id):
    """
        更新文章的视图函数
        通过POST方法提交表单，更新titile、body字段
        GET方法进入初始表单页面
        id： 文章的 id
        """
    # 获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id = id)
    # 过滤非作者的用户
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章。")
    #判断用户是否为post提交表单数据
    if request.method == "POST":
        #将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        #判断提交的数据是否满足模型要求
        if article_post_form.is_valid():
            #保存新写入的title，body数据保存
            article.title = request.POST['title']
            article.body = request.POST['body']
            article.save()
            #完成后返回到修改后的文章中，需要传入文章id值
            return redirect("article:article_detail",id=id)
        #如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写")
    else:
        #创建表单实例
        article_post_form = ArticlePostForm()
        context = {'article':article,'article_post_form':article_post_form}
        return render(request,'article/update.html',context)