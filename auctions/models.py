from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length = 64, unique = True)
    def __str__(self):
        return self.name

class AuctionListings(models.Model):
    title = models.CharField(max_length = 64)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="listings")
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    watcher = models.ManyToManyField(User, related_name="watchlist", blank=True)
    def __str__(self):
        return f"{self.title} by {self.owner}"

class Bids(models.Model):
    listing = models.ForeignKey(AuctionListings, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    largest_bid = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.bidder} bids {self.largest_bid} for {self.listing}"

class Comments(models.Model):
    text = models.CharField(max_length = 200)
    listing = models.ForeignKey(AuctionListings, on_delete = models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.commenter} commented about {self.listing}: {self.text}"