from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _
from .models import *


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ['id', 'username', 'first_name', 'last_name', 'type', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name','last_name', 'email' )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Extra'), {'fields': ('type', 'phone', 'company_name', 'country', 'street_address', 'postcode', 'town' )}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')})
    )

# admin.site.register(User)
admin.site.register(Info)
admin.site.register(Image)
admin.site.register(Email)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Review)
admin.site.register(ContactUs)
admin.site.register(Wishlist)
admin.site.register(Card)
admin.site.register(Comment)
admin.site.register(Blog)
admin.site.register(Blogtext)
admin.site.register(Abouttext)
admin.site.register(About)
admin.site.register(Reply)
admin.site.register(Delivery_Options)
admin.site.register(Order)
admin.site.register(Country)
