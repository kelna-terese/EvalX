import uuid
import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=[
        ('COORDINATOR', 'Coordinator'),
        ('HOD', 'HOD'),
        ('GUIDE', 'Guide'),
        ('TEAM', 'Team')
    ], default='TEAM')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"

class Team(models.Model):
    # Added blank=True so Django doesn't complain when the form is submitted without an ID
    team_id = models.CharField(max_length=15, primary_key=True, editable=False, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    guide = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='team_profile'
    )
    leader_name = models.CharField(max_length=100, blank=True, null=True)
    project_title = models.CharField(max_length=255, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.team_id:
            # 1. Get current year
            year = datetime.datetime.now().year
            prefix = f"TM{year}"

            # 2. Get the last team ID for this year to find the next number
            last_team = Team.objects.filter(team_id__startswith=prefix).order_by('team_id').last()
            
            if last_team:
                try:
                    # Extract last 2 digits, increment them
                    last_no = int(last_team.team_id[-2:])
                    new_no = last_no + 1
                except (ValueError, IndexError):
                    new_no = 1
            else:
                new_no = 1

            # 3. Final Format: TM202601
            self.team_id = f"{prefix}{new_no:02d}"

        super(Team, self).save(*args, **kwargs)

    def __str__(self):
        return self.team_id

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=100)
    reg_number = models.CharField(max_length=20, unique=True)
    is_leader = models.BooleanField(default=False)

    # ==========================================================
    # EVALUATION SHEET 1 - REVIEW 1 (40 Marks each)
    # ==========================================================
    # COORDINATOR REVIEW 1
    r1_c_comp = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_c_func = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r1_c_pres = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r1_c_oral = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_c_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_c_absent = models.BooleanField(default=False)

    # HOD REVIEW 1
    r1_h_comp = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_h_func = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r1_h_pres = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r1_h_oral = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_h_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_h_absent = models.BooleanField(default=False)

    # GUIDE REVIEW 1
    r1_g_comp = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_g_func = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r1_g_pres = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r1_g_oral = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_g_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r1_g_absent = models.BooleanField(default=False)

    # ==========================================================
    # EVALUATION SHEET 1 - REVIEW 2 (40 Marks each)
    # ==========================================================
    # COORDINATOR REVIEW 2
    r2_c_comp = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_c_func = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r2_c_pres = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r2_c_oral = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_c_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_c_absent = models.BooleanField(default=False)

    # HOD REVIEW 2
    r2_h_comp = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_h_func = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r2_h_pres = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r2_h_oral = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_h_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_h_absent = models.BooleanField(default=False)

    # GUIDE REVIEW 2
    r2_g_comp = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_g_func = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r2_g_pres = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    r2_g_oral = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_g_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    r2_g_absent = models.BooleanField(default=False)

    # ==========================================================
    # EVALUATION SHEET 2 (COORDINATOR ONLY - 15 Marks)
    # ==========================================================
    s2_teamwork = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(4)])
    s2_tech_know = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(6)])
    s2_regularity = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])

    # ==========================================================
    # REPORT MARKS & ATTENDANCE
    # ==========================================================
    report_guide = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    report_coord = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    report_hod = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Attendance entered manually by Coordinator (10)
    attendance_marks = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])

    # ==========================================================
    # CALCULATION PROPERTIES
    # ==========================================================

    r1_coord_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(40)])
    r1_hod_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(40)])
    r1_guide_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(40)])

    @property
    def r1_consolidated_40(self):
        """Average of Coordinator, HOD, and Guide for Review 1."""
        marks = [self.r1_coord_total, self.r1_hod_total, self.r1_guide_total]
        return sum(marks) / 3.0

    r2_coord_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(40)])
    r2_hod_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(40)])
    r2_guide_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(40)])

    @property
    def r2_consolidated_40(self):
        """Average for Review 2 - Fixed to ensure data shows even if partially filled."""
        marks = [self.r2_coord_total, self.r2_hod_total, self.r2_guide_total]
        return sum(marks) / 3.0

    # --- Final Sheet Totals ---
    @property
    def avg_evaluation_40(self):
        """(Review 1 Cons + Review 2 Cons) / 2."""
        return (self.r1_consolidated_40 + self.r2_consolidated_40) / 2.0

    @property
    def consolidated_report_marks(self):
        """(Guide + Coord + HOD) / 3 for Report section."""
        return (self.report_guide + self.report_coord + self.report_hod) / 3.0

    s2_total = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(15)])

    @property
    def final_internal_75(self):
        """
        Total Internal Marks Calculation:
        Sheet 2 (15) + Cons. Report (10) + Avg Eval (40) + Attendance (10) = 75
        """
        return (
            self.s2_total + 
            self.consolidated_report_marks + 
            self.avg_evaluation_40 + 
            self.attendance_marks
        )


    def __str__(self):
        return f"{self.name} ({self.reg_number})"
    
class DocumentSlot(models.Model):
    # --- ADDED SLOT TYPES ---
    SLOT_TYPES = (
        ('PROPOSAL', 'Project Proposal'),
        ('ABSTRACT', 'Abstract'),
        ('SRS', 'SRS Document'),
        ('FINAL_PPT', 'Final PPT'),
        ('REPORT', 'Final Project Report'),
    )
    title = models.CharField(max_length=100)
    deadline = models.DateTimeField(null=True, blank=True)
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPES, default='OTHER')
    is_active = models.BooleanField(default=True)
    
    # Review Dates for the Notifications sidebar
    review_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

class TeamSubmission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='submissions')
    slot = models.ForeignKey(DocumentSlot, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if not self.status:
            import django.utils.timezone as tz
            if timezone.now() <= self.slot.deadline:
                self.status = "On Time"
            else:
                self.status = "Late"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.team.team_id} - {self.slot.slot_type} - Approved: {self.is_approved}"