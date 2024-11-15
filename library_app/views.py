from django.shortcuts import render
from .models import Book, Member, Transaction
from django.http import JsonResponse
# import requests
from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Member
from django.contrib import messages
from django.db.models import Q
from datetime import datetime
from django.utils import timezone
from django.views import View

class create_book(View):
    def get(self,request):
        return render(request, 'create_book.html')

    def post(self,request):
        title = request.POST['title']
        author = request.POST['author']
        isbn = request.POST['isbn']
        publisher = request.POST['publisher']
        page_count = request.POST['pagecount']
        available = request.POST['Available']

        Book.objects.create(title=title, authors=author, isbn=isbn, publisher=publisher, page_count=page_count, available=available)
        messages.success(request, "Book added successfully!")
        return redirect('book_list')
    
class update_book(View):
    def get(self,request,pk):
        book = get_object_or_404(Book, pk=pk)
        return render(request, 'create_book.html', {'book': book})

    def post(self,request,pk):
        book = get_object_or_404(Book, pk=pk)
        book.title = request.POST['title']
        book.authors = request.POST['author']
        book.isbn = request.POST['isbn']
        book.page_count=request.POST['pagecount']
        book.available=request.POST['Available']
        book.save()
        messages.success(request, "Book updated successfully!")
        return redirect('book_list')

class delete_book(View):
    def get(self,request,pk):
        book = get_object_or_404(Book, pk=pk)
        book.delete()
        messages.success(request, "Book deleted successfully!")
        return redirect('book_list')

class book_list(View):
    def get(self,request):
        books = Book.objects.all()
        members = Member.objects.all()  
        transactions = Transaction.objects.all()
        

        return render(request, 'book_list.html', {'books': books, 'member': members,'transactions': transactions})

#------------------------------------------------------------------------------------------

class member_list(View):
    def get(self,request):
        members = Member.objects.all()
        return render(request, 'member_list.html', {'members': members})

class create_member(View):
    def get(self,request):
            return render(request, 'create_member.html')
    def post(self,request):        
        member_name = request.POST['name']
        member_mail = request.POST['email']
        Member.objects.create(name=member_name,email=member_mail)
        messages.success(request, "Member added successfully!")
        return redirect('member_list')

class delete_member(View):
    def get(self,request,member_id):
        member = get_object_or_404(Member, id=member_id)
        member.delete()
        return redirect('member_list')

# Issue a book to a member
#----------------------------------------------------------------------------
class issue_book(View):
    def get(self,request,book_id):
        book =Book.objects.get(id=book_id)
        members = Member.objects.all()
        return render(request,'issue_book.html',{"book":book,"members":members})
    
    def post(self,request,book_id):
        book =Book.objects.get(id=book_id)
        member =Member.objects.get(id=request.POST['member_id'])      
          
        if member.outstanding_debt > 500:
            messages.error(request, "Member's outstanding debt exceeds Rs. 500. Cannot issue book.")
            return redirect('book_list')
    
        if book.available:
            book.available = False  # Mark the book as unavailable
            book.save()

            Transaction.objects.create(book=book, member=member, issue_date=timezone.now())
            messages.success(request, f"Book '{book.title}' issued to {member.name} successfully!")
            return redirect('book_list')
        else:
            messages.error(request, f"Book '{book.title}' is not available for issuing.")
        


# def calculate_rental_fee(transaction):
#     borrowed_days = (timezone.now() - transaction.issue_date).days  # Both are timezone-aware now
#     print(borrowed_days)
#     if borrowed_days > 0:  # Assuming a 14-day loan period
#         overdue_days = borrowed_days - 14
#         print(overdue_days)
#         return overdue_days * 5  # Assuming Rs. 50/day fine
#     return 0  # No fee if returned within 14 days

from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from decimal import Decimal, InvalidOperation

class return_book(View):
    def get(self,request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)
        mem = Member.objects.get(id=transaction.member_id)
        book = transaction.book
        member = transaction.member
        context = {
            'book': book,
            'member': member,
        }
        return render(request, 'return_book.html', context)

    def post(self,request,transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)
        mem = Member.objects.get(id=transaction.member_id)
        book = transaction.book
        member = transaction.member




        
        try:
            # Get the return date from the POST request and convert it to a timezone-aware datetime object
            return_date_str = request.POST['return_date']
            return_date = datetime.strptime(return_date_str, '%Y-%m-%dT%H:%M')
            return_date = timezone.make_aware(return_date, timezone.get_current_timezone())  # Make the datetime timezone-aware

            borrow_date = transaction.issue_date  # Assuming issue_date is timezone-naive

            # Convert borrow_date to timezone-aware if it's naive
            if timezone.is_naive(borrow_date):
                borrow_date = timezone.make_aware(borrow_date, timezone.get_current_timezone())

            # Calculate the number of days the book was borrowed
            days_borrowed = (return_date - borrow_date).days

            # Default rental fee to Decimal('0') for cases where no fee is applicable
            rental_fee = Decimal('0')
            if days_borrowed > 14:
                extra_days = days_borrowed - 14
                rental_fee = Decimal(extra_days) * Decimal('50.00')  # Charge Rs.50 per extra day
            
            # Debugging outputs
            print(f"Return date: {return_date}, Borrow date: {borrow_date}")
            print(f"Days borrowed: {days_borrowed}, Rental fee: {rental_fee}")

            # Handle form submission
            book.available = True
            book.save()

            # Update outstanding debt using Decimal
            mem.outstanding_debt += rental_fee
            mem.save()

            transaction.return_date = return_date
            transaction.fee = rental_fee
            transaction.save()

            # Set a success message
            messages.success(request, f'Book "{book.title}" returned successfully. Rental fee: ₹{rental_fee}')
            
            # Redirect to the book list
            return redirect('book_list')

        except InvalidOperation as e:
            # Catch Decimal exceptions and display meaningful error messages
            messages.error(request, f'An error occurred with the decimal operation: {e}')
    
#------------------------------------------------------------------------------------------

def search_books(request):
    query = request.GET.get('q')
    books = Book.objects.filter(Q(title__icontains=query) | Q(authors__icontains=query))
    return render(request, 'book_list.html', {'books': books})

# Import Books from Frappe API
# def import_books(request, page=1, title=""):
#     url = "https://frappe.io/api/method/frappe-library?page=2&title=and"
#     params = {"page": page, "title": title}
#     response = requests.get(url, params=params)
    
#     if response.status_code == 200:
#         books = response.json()["message"]
#         for book in books:
#             Book.objects.create(
#                 title=book['title'],
#                 authors=book['authors'],
#                 isbn=book['isbn'],
#                 publisher=book['publisher'],
#                 page_count=book['  num_pages']
#             )
#         return JsonResponse({"status": "success", "imported_books": books})
#     else:
#         return JsonResponse({"status": "error", "message": "Failed to fetch data"})


class transaction_list(View):
    def get(self,request):
        transactions = Transaction.objects.all()
        data = {"transactions" : transactions} 

        return render(request,'Transaction_list.html',data)