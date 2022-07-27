from itertools import product
from multiprocessing import context
from unicodedata import category
from rest_framework.authtoken.models import Token
from django.shortcuts import render,redirect
import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view, APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView, CreateAPIView
from rest_framework import status
from django.http import Http404
from main.models import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import permission_classes,authentication_classes
from main.serializer import *
from django.contrib.auth import authenticate
from django.contrib.auth import login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from random import *
from .models import User as Users
import random 
import datetime



class CountryView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class EmailView(CreateAPIView):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer

class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ImageView(ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class Slider(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request):
        slider = Product.objects.all().order_by('-rating')[:5]
        ser = ProductSerializer(slider, many=True)
        return Response(ser.data)

@api_view(['GET'])
def latest_products(request):
    product = Product.objects.all().order_by("-id")[:6]
    prod = ProductSerializer(product, many=True)
    return Response(prod.data)

@api_view(['GET'])
def filter_by_price(request):
    st_price = request.GET.get('st_price')
    end_price = request.GET.get('end_price')
    pr = Product.objects.filter(price__gte=st_price, price__lte=end_price)
    p = ProductSerializer(pr, many=True)
    return Response(p.data)

class ProductDetail(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def retrieve(self, request, pk):
        pr = Product.objects.get(id=pk)
        products = Product.objects.filter(category=pr.category)
        DATA = {
            "Product":ProductSerializer(pr).data,
            "Similar Products":ProductSerializer(products,many=True).data,            
        }
        return Response(DATA)

class RewievGEt(APIView):
    def get(self, request):
        Data = {}
        all_products = Product.objects.all()
        for i in all_products:
            a = Review.objects.filter(product_id=i.id)
            for d in a:
                i.rating += d.rating
                Data[i.name] = i.rating/len(a)                
        return Response(Data)

class RewievPost(APIView):
    def post(self, request):
        try:
            rating = request.POST['rating']
            text = request.POST['text']
            product = request.POST['product']
            name = request.POST.get("name")
            email = request.POST.get("email")
            aaa = Review.objects.create(
                rating=rating,
                text=text,
                product_id=product,
                name=name,
                email=email,
            )
            aaa.save()
            all_products = Product.objects.all()
            for i in all_products:
                a = Review.objects.filter(product_id=i.id)
                if len(a) != 0:
                    i.rating = 0
                    for d in a:
                        i.rating += d.rating
                    i.rating = i.rating/len(a)
                    i.save()

            ab = ReviewSerializer(aaa)
            return Response(ab.data)
        except Exception as arr:
            data = {
                'error':f"{arr}"
            }
            return Response(data)

    
@api_view(['POST'])
def contactus(request):
    first_name = request.data['first_name']
    last_name = request.data['last_name']
    email = request.data['email']
    subject = request.data['subject']
    message = request.data['message']
    ContactUs.objects.create(
        first_name = first_name,
        last_name = last_name,
        email = email,
        subject = subject,
        message = message,
    )
    return Response(status=200)


# def Login(request):
#     if request.user.is_authenticated:
#         return redirect('home')
#     if request.method == "POST":
#         username =request.POST.get("username")
#         password = request.POST.get ('password')
#         employe = User.objects.filter(username=username)
#         if employe.count() > 0:
#             if employe[0].check_password(password):
#                 login(request,employe[0])


class CardView(APIView):
    def post(self, request):
        product = request.data['product']
        user = request.data['user']
        quantity = request.data['quantity']
        Card.objects.create(
            product_id=product,
            user_id=user,
            quantity=quantity,
        )
        return Response(status=200)
    
    def get(self, request):
        user = request.GET.get("user")
        uss = Card.objects.filter(user_id=user)
        us = CardSerializer(uss, many=True)
        return Response(us.data)
    
@api_view(['post'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def CheckOut(request):
    user = request.user
    carts = Card.objects.filter(user=user)
    address = user
    DATA = {
        "order":[],
        "bot_message":f"Имя: {user.first_name}\nФамилия: {user.last_name}\nemail: {user.email}\nНомер: {user.phone}\nАдрес: {address.country}, {address.street_address}\n",
    }
    total_price = 0
    for i in carts:
        data = Order.objects.create(
        email=user.email,
        delivery_address=user.street_address,
        contact = user.phone,
        product=i.product,
        quantity=i.quantity,
        )
        DATA['order'].append(OrderSerizlizer(data).data)
        DATA['bot_message'] += f"{i.product.name} dan {i.quantity} ta\n"
        total_price += i.product.price * i.quantity
        i.delete()
    DATA['bot_message'] += f"общий сумма: {total_price}"
    token = "5453955664:AAHmbCQcK4NKVevk5wWH1mE0FMG1ad8Dv8E"
    admin = "727134704"
    params = {
       "chat_id": admin,
       "text": DATA['bot_message'],
    }
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data=params)
    return Response(DATA['order'])


@api_view(['GET'])
def total_card(request):
    user = request.GET.get("user")
    card = Card.objects.filter(user_id=user)
    DATA = {
        "products":[],
        "total_price":0,
    }
    for i in card:
        DATA['total_price'] += i.product.price * i.quantity 
        ser = ProductSerializer(i.product)
        DATA['products'].append(ser.data) 
    
    return Response(DATA)



class WishlistView(APIView):
    def post(self, request):
        product = request.data['product']
        user = request.data['user']
        Wishlist.objects.create(
            product_id=product,
            user_id=user,
        )
        return Response(status=200)
    
    def get(self, request):
        user = request.GET.get("user")
        uss = Wishlist.objects.filter(user_id=user)
        us = WishlistSerializer(uss, many=True)
        return Response(us.data)


@api_view(['post'])
def Login(request):
    username =request.POST.get("username")
    password = request.POST.get ('password')
    try:
        user = Users.objects.get(username=username)
        if user.check_password(password):
            DATA = {
                "token":str(Token.objects.get(user=user))
            }
            return Response(DATA)
        else:
            return Response(status=401)
    except:
        return Response(status=401)

class BlogView(APIView):
    def get(self, request):
        blog = Blog.objects.all().order_by("-id")
        bl = BlogSerializer(blog, many=True)
        return Response(bl.data)


class BlogtextView(APIView):
    def post(self, request):
        text = BlogtextSerizlizer(data=request.data)
        if text.is_valid():
            text.save()
            return Response(text.data, status=status.HTTP_201_CREATED)
        return Response(text.errors, status=status.HTTP_400_BAD_REQUEST)


class AboutView(APIView):
    def get(self, request):
        about = About.objects.all().order_by("-id")
        bl = AboutSerizlizer(about, many=True)
        return Response(bl.data)


class AbouttextView(APIView):
    def post(self, request):
        text = AbouttextSerizlizer(data=request.data)
        if text.is_valid():
            text.save()
            return Response(text.data, status=status.HTTP_201_CREATED)
        return Response(text.errors, status=status.HTTP_400_BAD_REQUEST)


class ReplaySend(APIView):
    def post(self, request):
        replay = ReplySerizlizer(data=request.data)
        if replay.is_valid():
            replay.save()
            return Response(replay.data, status=status.HTTP_201_CREATED)
        return Response(replay.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentSend(APIView):
    def post(self, request):
        comment = CommentSerizlizer(data=request.data)
        if comment.is_valid():
            comment.save()
            return Response(comment.data, status=status.HTTP_201_CREATED)
        return Response(comment.errors, status=status.HTTP_400_BAD_REQUEST)



class OrderSend(APIView):
    def post(self, request):
        order = OrderSerizlizer(data=request.data)
        if order.is_valid():
            order.save()
            return Response(order.data, status=status.HTTP_201_CREATED)
        return Response(order.errors, status=status.HTTP_400_BAD_REQUEST)

@login_required

def Index(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    context = {
        "info": Info.objects.last(),
        'country':Country.objects.all().order_by("-id"),
        'order':Order.objects.all().order_by("-id"),
    }
    return render(request, 'index.html', context)

@login_required
def Productt(request):
    context = {
        'product': Product.objects.all().order_by('-id'),
        "info": Info.objects.last()

    }
    return render(request, 'product.html', context)

@login_required
def AddProductt(request):
    product = Product.objects.all().order_by('-id')
    images = Image.objects.all().order_by('-id')


    context = {
        "info": Info.objects.last(),
        'product':product,
        'images':images,
        'category':Category.objects.all().order_by("-id")
    }
    if request.method == 'POST':
        data = request.POST
        list = data.getlist("image")
        image = []
        for i in list:
            image.append(Image.objects.create(id=i))
        create = Product.objects.create(
            name = request.POST.get("name"),
            price = request.POST.get("price"),
            text = request.POST.get("text"),
            discount = request.POST.get("discount"),
            category = Category.objects.get(id=request.POST.get('category')),
            SKU = request.POST.get("SKU"),
            description = request.POST.get("description"),
            weight = request.POST.get("weight"),
            dimentions = request.POST.get("dimentions"),
            colours = request.POST.get("colours"),
            material = request.POST.get("material"),
            # is_active = request.POST.get("is_active"),
        )
        create.image.set(image)
        create.save()
        return redirect("product")


    return render(request, 'add-products.html', context)

@login_required
def EditProductt(request, pk):
    product = Product.objects.get(id=pk)
    if request.method == 'POST':
        product = Product.objects.get(id=pk)
        product.name = request.POST['name']
        product.price = request.POST['price']
        product.text = request.POST['text']
        product.discount = request.POST['discount']
        imgs = []
        for i in request.POST.getlist("images"):
            imgs.append(Image.objects.get(id=i))
        product.image.set(imgs)
        product.category = Category.objects.get(id=request.POST.get('category'))
        product.description = request.POST.get('description')
        product.weight = request.POST.get('weight')
        product.dimentions = request.POST.get('dimentions')
        product.colours = request.POST.get('colours')
        product.material = request.POST.get('material')
        product.save()
        return redirect("product")
    context = {
        'product': product,
        "info": Info.objects.last(),
        "categorys":Category.objects.all().order_by("-id"),
        "images":Image.objects.all(),
    }
    return render(request, 'product-edit.html', context)

@login_required        
def product_delete(request, pk):
    delete = Product.objects.get(id=pk)
    delete.delete()
    return redirect("product")
      
@login_required
def blog(request):
    context = {
        'blog': Blog.objects.all().order_by('-id'),
        'info': Info.objects.last(),
        'blogtext':Blogtext.objects.all().order_by("-id")
    }

    return render(request, 'blog.html', context)

@login_required
def add_blog(request):

    context = {
        'info': Info.objects.last(),
        'blog': Blog.objects.all(),
        'category': Category.objects.all().order_by("-id"),
        'blogtext':Blogtext.objects.all().order_by("-id")
    }
    if request.method == "POST":
        data = request.POST
        list = data.getlist("blogtext")
        bgt = []
        for i in list:
            bgt.append(Blogtext.objects.create(id=i))
        create = Blog.objects.create(
            img = request.FILES.get("img"),
            title = request.POST.get("title"),
            text = request.POST.get("text"),
            category = Category.objects.get(id=request.POST.get("category"))
        )
        create.blogtext.set(bgt)
        create.save()
        return redirect("blog")
    return render(request, 'add-blog.html', context)

@login_required        
def blog_delete(request, pk):
    delete = Blog.objects.get(id=pk)
    delete.delete()
    return redirect("blog")


@login_required
def edit_blog(request, pk):
    blog = Blog.objects.get(id=pk)
    if request.method == "POST":
        blog = Blog.objects.get(id=pk)
        blog.img = request.FILES.get("img")
        blog.title = request.POST.get("title")
        blog.text = request.POST.get("text")
        blog.category = Category.objects.get(id=request.POST.get("category"))
        txt = []
        for i in request.POST.getlist("blogtext"):
            txt.append(Blogtext.objects.get(id=i))
        blog.blogtext.set(txt)
        blog.save()
        return redirect("blog")
    
    context = {
        "blog":blog,
        'info':Info.objects.all().order_by("-id"),
        'category': Category.objects.all().order_by("-id"),
        'blogtext':Blogtext.objects.all().order_by("-id")
    }
    return render(request, "edit-blog.html", context)









    
@login_required
def about(request):

    context = {
        'info': Info.objects.last(),
        'about':About.objects.all().order_by("-id"),
        'abouttext':Abouttext.objects.all().order_by("-id")
    }

    return render(request, 'about.html', context)

@login_required
def add_about(request):
    context = {
        'info': Info.objects.last(),
        'about':About.objects.all().order_by("-id"),
        'category': Category.objects.all().order_by("-id"),
        'abouttext':Abouttext.objects.all().order_by("-id")

    }
    if request.method == "POST":
        data = request.POST
        list = data.getlist("abouttext")
        bgt = []
        for i in list:
            bgt.append(Abouttext.objects.get(id=i))
        print(request.FILES["img"])
        create = About.objects.create(
            img = request.FILES["img"],
            title = request.POST.get("title"),
            text = request.POST.get("text"),
            category = Category.objects.get(id=request.POST.get("category"))
        )
        create.abouttext.set(bgt)
        create.save()
        return redirect("about")

    return render(request, 'add-about.html', context)
@login_required
def edit_about(request, pk):
    about = About.objects.get(id=pk)
    if request.method == "POST":
        about = About.objects.get(id=pk)
        if "img" in request.FILES:
            about.img = request.FILES.get("img")

        about.title = request.POST.get("title")
        about.text = request.POST.get("text")
        about.category = Category.objects.get(id=request.POST.get("category"))
        txt = []
        for i in request.POST.getlist("abouttext"):
            txt.append(Abouttext.objects.get(id=i))
        about.abouttext.set(txt)
        about.save()
        return redirect("about")
    
    context = {
        "about":about,
        'info':Info.objects.last(),
        'category': Category.objects.all().order_by("-id"),
        'abouttext':Abouttext.objects.all().order_by("-id")
    }
    return render(request, "edit-about.html", context)

@login_required        
def about_delete(request, pk):
    delete = About.objects.get(id=pk)
    delete.delete()
    return redirect("about")

@login_required
def country(request):
    context = {
        'info':Info.objects.last(),
        "country": Country.objects.all().order_by("-id"),
    }
    return render(request, "country.html", context)
@login_required    
def add_country(request):
    if request.method == "POST":
        name = request.POST['name']
        Country.objects.create(name=name)
        return redirect("country")
    context = {
        "country": Country.objects.all().order_by("-id"),
        'info':Info.objects.last(),
    }
    return render(request, "add-country.html", context)

@login_required
def edit_country(request, pk):
    country = Country.objects.get(id=pk)
    if request.method == "POST":
        country = Country.objects.get(id=pk)
        country.name = request.POST.get("name")
        country.save()
        return redirect('country')
    context = {
        "country": country,
        'info':Info.objects.last(),
    }
    return render(request, "edit-country.html", context)


@login_required        
def country_delete(request, pk):
    delete = Country.objects.get(id=pk)
    delete.delete()
    return redirect("country")

@login_required
def info(request):
    cn = {
        'info': Info.objects.all().order_by("-id")
    }
    return render(request, 'info.html', cn)
@login_required
def add_info(request):
    context = {
        'info': Info.objects.last()

    }
    if request.method == "POST":
        Info.objects.create(
            logo = request.FILES["logo"],
            in_link = request.POST.get("in_link"),
            tw_link = request.POST.get("tw_link"),
            fa_link = request.POST.get("fa_link"),
            insta_link = request.POST.get("insta_link"),
        )
        return redirect("info")

    return render(request, 'add-info.html', context)
@login_required
def edit_info(request, pk):
    info = Info.objects.get(id=pk)
    if request.method == "POST":
        info = Info.objects.get(id=pk)
        if "logo" in request.FILES:
            info.logo = request.FILES.get("logo")
        info.in_link = request.POST.get("in_link")
        info.tw_link = request.POST.get("tw_link")
        info.fa_link = request.POST.get("fa_link")
        info.insta_link = request.POST.get("insta_link")
        info.save()
        return redirect("info")
    cn = {
        "info":info
    }
    return render(request, "edit-info.html", cn)




@login_required
def info_delete(request, pk):
    delete = Info.objects.get(id=pk)
    delete.delete()
    return redirect("info")
@login_required
def email(request):
    cn = {
        'info':Info.objects.last(),
        'email':Email.objects.all().order_by("-id")
    }
    return render(request, 'email.html', cn)


@login_required
def email_delete(request, pk):
    delete = Email.objects.get(id=pk)
    delete.delete()
    return redirect("email")

@login_required
def category(request):
    context = {
        'info':Info.objects.last(),
        "category": Category.objects.all().order_by("-id"),
    }
    return render(request, "category.html", context)
  
@login_required
def add_category(request):
    if request.method == "POST":
        name = request.POST['name']
        Category.objects.create(name=name)
        return redirect("category")
    context = {
        "category": Category.objects.all().order_by("-id"),
        'info':Info.objects.last(),
    }
    return render(request, "add-category.html", context)

@login_required
def edit_category(request, pk):
    category = Category.objects.get(id=pk)
    if request.method == "POST":
        category = Category.objects.get(id=pk)
        category.name = request.POST.get("name")
        category.save()
        return redirect('category')
    context = {
        "category": category,
        'info':Info.objects.last(),
    }
    return render(request, "edit-category.html", context)

@login_required        
def category_delete(request, pk):
    delete = Category.objects.get(id=pk)
    delete.delete()
    return redirect("category")

@login_required
def imagess(request):
    cn = {
        'info':Info.objects.last(),
        'image':Image.objects.all().order_by("-id"),
    }
    return render(request, 'image.html', cn)
@login_required
def add_image(request):
    if request.method == "POST":
        image = request.POST.get('image')
        Image.objects.create(image=image)
        return redirect("image")
    context = {
        "image": Image.objects.all().order_by("-id"),
        'info':Info.objects.last(),
    }
    return render(request, "add-image.html", context)

@login_required
def edit_image(request, pk):
    image = Image.objects.get(id=pk)
    if request.method == "POST":
        image = Image.objects.get(id=pk)
        if "image" in request.FILES:
            image.image = request.FILES.get("image")
        image.save()
        return redirect('image')
    context = {
        "image": image,
        'info':Info.objects.last(),
    }
    return render(request, "edit-image.html", context)

@login_required
def image_delete(request, pk):
    delete = Image.objects.get(id=pk)
    delete.delete()
    return redirect("image")

@login_required
def review(request):
    con = {
        'review':Review.objects.all().order_by("-id"),
        'info':Info.objects.last(),
        'product':Product.objects.all().order_by("-id"),
    }
    return render(request, "review.html", con)
@login_required
def add_review(request):
    if request.method == "POST":
        Review.objects.create(
            rating = request.POST.get("rating"),
            text = request.POST.get("text"),
            name = request.POST.get("name"),
            email = request.POST.get("email"),
            product = Product.objects.get(id=request.POST.get('product')),
            
        )
        return redirect("review")
 
    con = {
        'product':Product.objects.all().order_by("-id"),
        'info':Info.objects.last(),
        'review':Review.objects.all().order_by("-id"),

    }
    return render(request, "add-review.html", con)
     
@login_required
def edit_review(request, pk):
    review = Review.objects.get(id=pk)
    if request.method == "POST":
        review = Review.objects.get(id=pk)
        review.name = request.POST.get("name")
        review.text = request.POST.get("text")
        review.email = request.POST.get("email")
        review.rating = request.POST.get("rating")
        review.product = Product.objects.get(id=request.POST.get('product'))
        review.save()
        return redirect('review')
    context = {
        "review": review,
        'info':Info.objects.last(),
        'product':Product.objects.all().order_by("-id") 
    }
    return render(request, "edit-review.html", context)

@login_required
def review_delete(request, pk):
    delete = Review.objects.get(id=pk)
    delete.delete()
    return redirect("review")

@login_required
def contactus(request):
    context = {
        'info':Info.objects.last(),
        "contactus": ContactUs.objects.all().order_by("-id"),
    }
    return render(request, "contactus.html", context)
@login_required  
def contactus_delete(request, pk):
    delete = ContactUs.objects.get(id=pk)
    delete.delete()
    return redirect("contactus")

@login_required
def reply(request):
    con = {
        'info':Info.objects.last(),
        'reply':Reply.objects.all().order_by("-id"),
        'blog':Blog.objects.all().order_by("-id")
    }
    return render(request, "reply.html", con)

@login_required  
def reply_delete(request, pk):
    delete = Reply.objects.get(id=pk)
    delete.delete()
    return redirect("reply")
@login_required    
def comment(request):
    con = {
        'info':Info.objects.last(),
        'reply':Reply.objects.all().order_by("-id"),
        'comment':Comment.objects.all().order_by("-id"),
    }
    return render(request, "comment.html", con)

@login_required
def comment_delete(request, pk):
    delete = Comment.objects.get(id=pk)
    delete.delete()
    return redirect("comment")

@login_required
def blogtext(request):
    context = {
        "blogtext":Blogtext.objects.all().order_by("-id"),
        "info": Info.objects.last()
    }
    return render(request, "blogtext.html", context)

@login_required
def add_blogtext(request):
    if request.method == "POST":
        text = request.POST['text']
        Blogtext.objects.create(text=text)
        return redirect("blogtext")
    context = {
        "blogtext": Blogtext.objects.all().order_by("-id"),
        'info':Info.objects.last()
    }
    return render(request, "add-blogtext.html", context)

@login_required
def edit_blogtext(request, pk):
    blogtext = Blogtext.objects.get(id=pk)
    if request.method == "POST":
        blogtext = Blogtext.objects.get(id=pk)
        blogtext.text = request.POST.get("text")
        blogtext.save()
        return redirect('blogtext')
    context = {
        "blogtext": blogtext,
        'info':Info.objects.last()
    }
    return render(request, "edit-blogtext.html", context)

@login_required
def blogtext_delete(request, pk):
    delete = Blogtext.objects.get(id=pk)
    delete.delete()
    return redirect("blogtext")

@login_required
def abouttext(request):
    context = {
        "abouttext":Abouttext.objects.all().order_by("-id"),
        "info": Info.objects.last()
    }
    return render(request, "abouttext.html", context)

@login_required
def add_abouttext(request):
    if request.method == "POST":
        text = request.POST['text']
        Abouttext.objects.create(text=text)
        return redirect("abouttext")
    context = {
        "abouttext": Abouttext.objects.all().order_by("-id"),
        'info':Info.objects.last()
    }
    return render(request, "add-abouttext.html", context)

@login_required
def edit_abouttext(request, pk):
    abouttext = Abouttext.objects.get(id=pk)
    if request.method == "POST":
        abouttext = Abouttext.objects.get(id=pk)
        abouttext.text = request.POST.get("text")
        abouttext.save()
        return redirect('abouttext')
    context = {
        "abouttext": abouttext,
        'info':Info.objects.last()
    }
    return render(request, "edit-abouttext.html", context)

@login_required
def abouttext_delete(request, pk):
    delete = Abouttext.objects.get(id=pk)
    delete.delete()
    return redirect("abouttext")

@login_required
def delivery_options(request):
    context = {
        "delivery_options":Delivery_Options.objects.all().order_by("-id"),
        "info": Info.objects.last()
    }
    return render(request, "delivery_options.html", context)

@login_required
def add_delivery_options(request):
    if request.method == "POST":
        delivery = request.POST['delivery']
        Delivery_Options.objects.create(delivery=delivery)
        return redirect("delivery_options")
    context = {
        "delivery_options": Delivery_Options.objects.all().order_by("-id"),
        'info':Info.objects.last()
    }
    return render(request, "add-delivery_options.html", context)

@login_required
def edit_delivery_options(request, pk):
    delivery_options = Delivery_Options.objects.get(id=pk)
    if request.method == "POST":
        delivery_options = Delivery_Options.objects.get(id=pk)
        delivery_options.delivery = request.POST.get("delivery")
        delivery_options.save()
        return redirect('delivery_options')
    context = {
        "delivery_options": delivery_options,
        'info':Info.objects.last()
    }
    return render(request, "edit-delivery_options.html", context)

@login_required
def delivery_options_delete(request, pk):
    delete = Delivery_Options.objects.get(id=pk)
    delete.delete()
    return redirect("delivery_options")


@login_required
def order(request):

    context = {
        'order':Order.objects.all().order_by("-id"),
        'delivery_options':Delivery_Options.objects.all().order_by("-id"),
        'product':Product.objects.all().order_by("-id"),
        'info':Info.objects.last()
    }


    return render(request, "order.html", context)
@login_required
def add_order(request):
    context = {
        'order':Order.objects.all().order_by("-id"),
        'delivery_options':Delivery_Options.objects.all().order_by("-id"),
        'product':Product.objects.all().order_by("-id"),
        'info':Info.objects.last()
    }

    if request.method == 'POST':
        Order.objects.create(
            email = request.POST.get("email"),
            status = request.POST.get("status"),
            delivery_address = request.POST.get("delivery_address"),
            contact = request.POST.get("contact"),
            delivery_options = Delivery_Options.objects.get(id=request.POST.get('delivery_options')),
            product = Product.objects.get(id=request.POST.get('product')),
            quantity = request.POST.get("quantity"),
        )
        return redirect("order")

    return render(request, 'add-order.html', context)


def web_Login(request):
    print(request.user.is_authenticated)
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        print('post')
        username =request.POST.get("username")
        password = request.POST.get ('password')
        employe = Users.objects.filter(username=username)
        if employe.count() > 0:
            if employe[0].check_password(password):
                login(request,employe[0])
                return redirect("home")
            else:
                return redirect('login')
        else:
            return redirect('login')    
    return render(request, 'login.html')