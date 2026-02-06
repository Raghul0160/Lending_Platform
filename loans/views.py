import razorpay
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.conf import settings
from .models import Loan, UserProfile, EMI
from .forms import UserRegistrationForm, FullProfileForm, LoanApplyForm

RAZORPAY_KEY_ID = 'rzp_test_YOUR_KEY_HERE'
RAZORPAY_KEY_SECRET = 'YOUR_SECRET_HERE'

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))




def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})




@login_required
def profile_view(request):
   
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = FullProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile') 
    else:
        
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
        form = FullProfileForm(instance=profile, initial=initial_data)

    return render(request, 'modules/profile.html', {'form': form, 'profile': profile})

@login_required
def update_kyc(request):
   
    return redirect('profile')




@login_required
def apply_loan(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    
    if not profile.aadhar_number:
        return redirect('profile')

    if request.method == 'POST':
        form = LoanApplyForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.borrower = request.user
            loan.save()
            return redirect('dashboard')
    else:
        form = LoanApplyForm()
    
    return render(request, 'apply.html', {'form': form})



@login_required
def dashboard(request):
    
    loans = Loan.objects.filter(borrower=request.user)
    return render(request, 'dashboard.html', {'loans': loans})

@login_required
def my_loans_view(request):
  
    loans = Loan.objects.filter(borrower=request.user)
    return render(request, 'modules/my_loans.html', {'loans': loans})



@login_required
def payments_view(request):
    pending_emis = EMI.objects.filter(loan__borrower=request.user, is_paid=False).order_by('due_date')
    
    return render(request, 'modules/payments.html', {
        'emis': pending_emis,
        'razorpay_key': RAZORPAY_KEY_ID
    })

@login_required
def initiate_payment(request, emi_id):

    try:
        emi = EMI.objects.get(id=emi_id, loan__borrower=request.user)
    except EMI.DoesNotExist:
        return redirect('payments')

    amount_in_paise = int(emi.amount * 100)
    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1'
    }
    order = client.order.create(data=order_data)

    return render(request, 'modules/pay_confirm.html', {
        'order': order,
        'emi': emi,
        'razorpay_key': RAZORPAY_KEY_ID
    })

@csrf_exempt
def payment_success(request):
    if request.method == "POST":

        emi_id = request.POST.get('emi_id')
        
        if emi_id:
            try:
                emi = EMI.objects.get(id=emi_id)
                emi.is_paid = True
                emi.save()
                return render(request, 'modules/success.html')
            except EMI.DoesNotExist:
                pass
                
    return redirect('payments')



@login_required
def notifications_view(request):
    return render(request, 'modules/notifications.html')

@login_required
def transaction_history_view(request):
    # Get all EMIs that have been marked as PAID
    transactions = EMI.objects.filter(loan__borrower=request.user, is_paid=True).order_by('-due_date')
    return render(request, 'modules/history.html', {'transactions': transactions})

@login_required
def support_view(request):
    return render(request, 'modules/support.html')