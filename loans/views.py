import razorpay
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.conf import settings
from .models import Loan, UserProfile, EMI
from .forms import UserRegistrationForm, FullProfileForm, LoanApplyForm
from django.contrib import messages
from .utils import send_otp_email
from .models import OTP, User
from django.contrib import messages
from .utils import send_otp_email
from .models import OTP
from datetime import date
from .models import EMI

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
    today = date.today()
    
    # 1. Fetch all unpaid EMIs for this user
    all_unpaid = EMI.objects.filter(loan__borrower=request.user, is_paid=False).order_by('due_date')
    
    # 2. Categorize them
    overdue_emis = []
    current_emis = []
    upcoming_emis = []
    
    for emi in all_unpaid:
        if emi.due_date < today:
            overdue_emis.append(emi)
        elif emi.due_date.month == today.month and emi.due_date.year == today.year:
            current_emis.append(emi)
        else:
            upcoming_emis.append(emi)
            
    context = {
        'overdue': overdue_emis,
        'current': current_emis,
        'upcoming': upcoming_emis,
        'today': today,
        'razorpay_key': RAZORPAY_KEY_ID
    }
    
    return render(request, 'modules/payments.html', context)

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

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user but DO NOT activate yet
            user = form.save(commit=False)
            user.is_active = False 
            user.save()

            # Send OTP
            if send_otp_email(user.email):
                # Store email in session to know who is verifying
                request.session['registration_email'] = user.email
                return redirect('verify_registration')
            else:
                messages.error(request, "Error sending email. Check your internet connection.")
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

# --- 2. NEW VERIFY VIEW ---
def verify_registration(request):
    # Get the email from the session (saved in previous step)
    email = request.session.get('registration_email')
    
    if not email:
        return redirect('register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        
        try:
            user = User.objects.get(email=email)
            otp_record = OTP.objects.filter(user=user).last()
            
            if otp_record and otp_record.otp_code == entered_otp:
                # SUCCESS: Activate User
                user.is_active = True
                user.save()
                
                # Clean up OTP
                otp_record.delete()
                
                # Log them in
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid OTP Code. Please try again.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return render(request, 'registration/verify_otp.html', {'email': email})

# --- NEW: FORGOT PASSWORD ---
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            send_otp_email(email)
            request.session['reset_email'] = email
            return redirect('reset_password')
        else:
            messages.error(request, "Email not found in our system.")
            
    return render(request, 'registration/forgot_password.html')

# --- NEW: RESET PASSWORD ---
def reset_password(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
        
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        new_pass = request.POST.get('new_password')
        
        user = User.objects.get(email=email)
        db_otp = OTP.objects.filter(user=user).last()
        
        if db_otp and db_otp.otp_code == otp_input:
            user.set_password(new_pass)
            user.save()
            db_otp.delete()
            messages.success(request, "Password reset successful! Please login.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP code.")
            
    return render(request, 'registration/reset_password.html', {'email': email})