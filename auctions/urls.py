from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("listings/<int:id>",views.listing_page, name="listing_page"),
    path("watchlist", views.watchlist_view, name="watchlist_view"),
    path("watchlist/<int:id_number>", views.watchlist_adjust, name="watchlist_adjust"),
    path("bid/<int:id_number>", views.bid, name="bid"),
    path("close/<int:id>", views.close_listing, name="close_listing"),
    path("write_comments/<int:id>", views.write_comments, name="write_comments"),
    path("search", views.search, name="search"),
    path("category/<str:type_category>", views.category, name="category"),
    path("categories_view", views.categories_view, name="categories_view")
]
