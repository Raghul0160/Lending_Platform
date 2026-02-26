from django.contrib import admin
from .models import UserProfile, LoanCategory, Loan, EMI


@admin.register(UserProfile)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'aadhar_number', 'is_kyc_verified')
    list_editable = ('is_kyc_verified',)
    search_fields = ('user__username', 'pan_number')


@admin.register(LoanCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'interest_rate', 'max_amount')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'borrower', 'category', 'amount', 'status')
    list_filter = ('status', 'category')
    actions = ['approve_loans']

    def approve_loans(self, request, queryset):
        queryset.update(status='approved')
        for loan in queryset: loan.save() 
    approve_loans.short_description = "Approve Selected Loans"


@admin.register(EMI)
class EMIAdmin(admin.ModelAdmin):
    list_display = ('loan', 'due_date', 'amount', 'is_paid')
    list_filter = ('is_paid', 'due_date')
    
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('is_paid', 'due_date')