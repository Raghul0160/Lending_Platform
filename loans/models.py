from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from dateutil.relativedelta import relativedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    aadhar_number = models.CharField(max_length=12, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    dob = models.DateField(null=True, blank=True) 
    is_kyc_verified = models.BooleanField(default=False)
    @property
    def age(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return "N/A"

    def __str__(self):
        return self.user.username

class LoanCategory(models.Model):
    name = models.CharField(max_length=50) 
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) 
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.name


class Loan(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Active'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    )
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(LoanCategory, on_delete=models.PROTECT, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure_months = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.borrower} - {self.category} - {self.amount}"


class EMI(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='emis')
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"EMI for Loan {self.loan.id}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=Loan)
def generate_emis(sender, instance, created, **kwargs):
    if instance.status == 'approved' and not instance.emis.exists():
        monthly_amount = instance.amount / instance.tenure_months 
        start_date = date.today()
        for i in range(1, instance.tenure_months + 1):
            EMI.objects.create(
                loan=instance,
                due_date=start_date + relativedelta(months=i),
                amount=monthly_amount
            )
            