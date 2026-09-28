from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from .models import User, Category, AuctionListings, Bids, Comments


def index(request):
    return render(request, "auctions/index.html", {
        "lists": AuctionListings.objects.all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "error_message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create(request):
    categories = Category.objects.all()
    if request.method == "POST":
        try:
            category_name = request.POST.get("category","").strip()     # remove whitespace from both ends of text
            if category_name:
                category, _ = Category.objects.get_or_create(name = category_name)      #get_or_create return the object and a boolean. True if created
            else:
                category = None
            title = request.POST["title"]
            description = request.POST["description"]
            image_url = request.POST.get("image_url", "")       # second parameter will be used if the image_url is empty
            category = category
            starting_bid = request.POST["starting_bid"]

            listing = AuctionListings.objects.create(
            title = title,
            description = description,
            image_url = image_url,
            category = category,
            starting_bid = starting_bid,
            owner = request.user        # request.user is by default
            )
            return HttpResponseRedirect(reverse("index"))
        except Exception as e:
            return render(request, "auctions/create.html", {
                "categories": categories,
                "error_message": "Unable to create this listing. Please fill out the entire form!"
            })

    return render(request, "auctions/create.html", {
        "categories": categories
    })


def listing_page(request, id):
    item = AuctionListings.objects.get(pk=id)
    all_comments = item.comments.all()
    if item.bids.exists():
        highest_bid = item.bids.order_by("-largest_bid").first()
        current_bid = highest_bid.largest_bid
        if item.is_active == False:
            if request.user == highest_bid.bidder:
                bid_message = "You won this item!"
            elif request.user == item.owner:
                bid_message = "You closed this listing!"
            else:
                bid_message = "The bid is no longer active."
        elif request.user == highest_bid.bidder:
            bid_message = "You bid is the current bid."
        else:
            bid_message = ""
    else:
        current_bid = item.starting_bid
        if item.is_active == False:
            bid_message = "The bid is no longer active."
        else:
            bid_message = ""
    return render(request, "auctions/listing_page.html", {
        "listing": item,
        "current_bid": current_bid,
        "bid_message": f"{item.bids.count()} bid(s) so far. {bid_message}",
        "comments": all_comments
    })


@login_required
def watchlist_adjust(request, id_number):
    if request.method == "POST":
        listing = AuctionListings.objects.get(pk=id_number)
        if request.user in listing.watcher.all():
            listing.watcher.remove(request.user)
        else:
            listing.watcher.add(request.user)
    return HttpResponseRedirect(reverse("listing_page", args=[id_number]))


@login_required
def watchlist_view(request):
    watchlists = request.user.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "lists": watchlists
    })


@login_required
def bid(request, id_number):
    if request.method == "POST":
        new_bid = Decimal(request.POST["new_bid"])
        item = AuctionListings.objects.get(pk=id_number)
        if item.bids.exists():
            highest_bid = item.bids.order_by("-largest_bid").first()
            current_bid = Decimal(highest_bid.largest_bid)
        else:
            current_bid = item.starting_bid

        if new_bid <= current_bid:
            return render(request, "auctions/listing_page.html",{
                "listing": item,
                "current_bid": current_bid,
                "count_bid": item.bids.count(),
                "error_message": f"Your bid must be greater than ${current_bid:,.2f}."
            })
        else:
            Bids.objects.create(
                listing = item,
                bidder = request.user,
                largest_bid = new_bid
            )
            return HttpResponseRedirect(reverse("listing_page", args=[id_number]))


@login_required
def close_listing(request, id):
    if request.method == "POST":
        item = AuctionListings.objects.get(pk=id)
        if item.is_active == True:
            item.is_active = False
            item.save()
        else:
            item.is_active = True
            item.save()
        return HttpResponseRedirect(reverse("listing_page", args=[id]))


@login_required
def write_comments(request, id):
    item = AuctionListings.objects.get(pk=id)
    if request.method == "POST":
        new_comment = Comments.objects.create(
            text = request.POST.get("comments"),
            listing = item,
            commenter = request.user
        )
        return HttpResponseRedirect(reverse("listing_page", args=[id]))


def search(request):
    listings = AuctionListings.objects.all()
    if request.method == "GET":
        search_item = request.GET["search"]
        if search_item:
            for listing in listings:
                if search_item.lower() == listing.title.lower():
                    return HttpResponseRedirect(reverse("listing_page", args=[listing.id]))
            matches = [listing for listing in listings if search_item.lower() in listing.title.lower()]
            if matches:
                return render(request, "auctions/search_view.html", {
                    "search_item": search_item,
                    "lists": matches
                })
            else:
                return render(request, "auctions/search_view.html", {
                    "search_item": search_item,
                    "message": "No items match your search!"
                })
        else:
            return HttpResponseRedirect(reverse("index"))


def category(request, type_category):
    # lists = AuctionListings.objects.filter(category__name = type_category)
    category_id = Category.objects.get(name = type_category).id
    lists = AuctionListings.objects.filter(category = category_id)
    return render(request, "auctions/category.html", {
        "category": type_category,
        "lists": lists
    })


def categories_view(request):
    lists = Category.objects.all().order_by("name")
    return render(request, "auctions/categories_view.html", {
        "categories": lists
    })