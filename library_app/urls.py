from django.urls import path, include
from .views import *

urlpatterns = [
    # path('import_books/',import_books),

    path('', book_list.as_view(), name='book_list'),
    path('books/add/', create_book.as_view(), name='create_book'),
    path('books/update/<int:pk>/', update_book.as_view(), name='update_book'),
    path('books/delete/<int:pk>/', delete_book.as_view(), name='delete_book'),

    path('books/issue/<int:book_id>/',issue_book.as_view(), name='issue_book'),
    path('books/return/<int:transaction_id>/',return_book.as_view(), name='return_book'),
    path('books/search/', search_books, name='search_books'),
    
    path('members/', member_list.as_view(), name='member_list'),
    path('members/add/', create_member.as_view(), name='create_member'),
    path('members/<int:member_id>/delete/', delete_member.as_view(), name='delete_member'),

    path('transaction_list/', transaction_list.as_view(), name='transaction_list'),


]
