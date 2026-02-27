from django.shortcuts import render 

from rest_framework import generics
from .models import Item
from .serializers import ItemSerializer

class ItemListCreate(generics.ListCreateAPIView):
    """View for listing and creating items"""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating and deleting items"""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

# Create your views here.
