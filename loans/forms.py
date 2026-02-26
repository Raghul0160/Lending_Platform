from datetime import date 
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Loan, LoanCategory


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    
    # New Field for Age Check
    dob = forms.DateField(
        label="Date of Birth",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'dob']

    # --- VALIDATION: CHECK AGE > 18 ---
    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        today = date.today()
        
        # Calculate Age
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age < 18:
            raise forms.ValidationError("Sorry, you must be at least 18 years old to register.")
        
        return dob

    # --- SAVE LOGIC ---
    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            if hasattr(user, 'profile'):
                user.profile.dob = self.cleaned_data['dob']
                user.profile.save()
                
        return user



class FullProfileForm(forms.ModelForm):
   
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    dob = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(attrs={'type': 'date'}), 
        required=True
    )

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'dob', 'address', 'aadhar_number', 'pan_number']

   
    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar:
           
            if len(aadhar) != 12 or not aadhar.isdigit():
                raise forms.ValidationError("Invalid Aadhar! Must be exactly 12 digits.")
        return aadhar

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number')
        if pan:
            if len(pan) != 10:
                raise forms.ValidationError("Invalid PAN! Must be 10 characters.")
            return pan.upper() 
        return pan

    
    def save(self, commit=True):
        profile = super(FullProfileForm, self).save(commit=False)
        
       
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
        return profile



class KYCForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'aadhar_number', 'pan_number']



class LoanApplyForm(forms.ModelForm):
   
    monthly_salary = forms.IntegerField(
        label="Your Monthly Salary ($)", 
        required=True,
        min_value=1000,
        widget=forms.NumberInput(attrs={'id': 'id_salary', 'oninput': 'calculateLimit()'})
    )
    
   
    category = forms.ModelChoiceField(
        queryset=LoanCategory.objects.all(),
        widget=forms.Select(attrs={'id': 'id_category', 'onchange': 'updateInterest()'})
    )
    
    amount = forms.DecimalField(
        label="Loan Amount Required ($)",
        widget=forms.NumberInput(attrs={'id': 'id_amount'})
    )

    tenure_months = forms.IntegerField(
        label="Tenure (Months)",
        widget=forms.NumberInput(attrs={'id': 'id_tenure'})
    )

    class Meta:
        model = Loan
        fields = ['monthly_salary', 'category', 'amount', 'tenure_months']

   
    def clean(self):
        cleaned_data = super().clean()
        salary = cleaned_data.get('monthly_salary')
        amount = cleaned_data.get('amount')

        if salary and amount:
           
            max_limit = salary * 20
            if amount > max_limit:
                raise forms.ValidationError(f"Eligibility Failed: Based on your salary, your max loan limit is ${max_limit}")
        
        return cleaned_data