import os
import random, string
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import openpyxl
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from .models import User, Team, TeamMember, DocumentSlot, TeamSubmission
from django.db.models import Count
from django.template.loader import render_to_string
from xhtml2pdf import pisa

def portal_gatekeeper(request):
    """The 4-panel landing page."""
    return render(request, 'accounts/portal_gatekeeper.html')

# accounts/views.py
from django.db.models import Count
import random, string

def register_team(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        l_name = request.POST.get('leader_name')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/register.html')

        try:
            # 1. Create User
            user = User.objects.create_user(email=email, username=email, password=password, role='TEAM')
            
            # 2. Allocate Guide (Load Balancing Logic)
            # We count 'team_profile' (your related_name) and order by the lowest count
            guides = User.objects.filter(role='GUIDE').annotate(
                t_count=Count('team_profile')
            ).order_by('t_count','id')
            
            # Select the guide with the absolute least number of teams
            assigned_guide = guides.first()
            
            if not assigned_guide:
                # Fallback if no guides are in the database yet
                user.delete() # Rollback user creation if no guide can be assigned
                messages.error(request, "Registration failed: No Faculty Guides are currently available.")
                return render(request, 'accounts/register.html')

            # 3. Create Team
            t_id = 'TM' + ''.join(random.choices(string.digits, k=5))
            team = Team.objects.create(
                team_id=t_id,
                user=user,
                guide=assigned_guide, # The guide with the least teams is now assigned
                leader_name=l_name
            )

            # 4. Save Members
            for i in range(1, 5):
                name = request.POST.get(f'm{i}_name')
                reg = request.POST.get(f'm{i}_reg')
                if name and reg:
                    TeamMember.objects.create(
                        team=team,
                        name=name,
                        reg_number=reg,
                        is_leader=(name == l_name)
                    )

            messages.success(request, f"Successfully Registered! Team ID: {t_id}")
            return redirect('team_login')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return render(request, 'accounts/register.html')

    return render(request, 'accounts/register.html')

def coordinator_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user and user.role == 'COORDINATOR':
            login(request, user)
            return redirect('coordinator_dashboard')
        messages.error(request, "Invalid credentials or not a Coordinator.")
    return render(request, 'accounts/login_coordinator.html')

def hod_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user and user.role == 'HOD':
            login(request, user)
            return redirect('hod_dashboard') # Ensure this URL name exists
        messages.error(request, "Invalid credentials or not an HOD.")
    return render(request, 'accounts/login_hod.html')

def guide_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user and user.role == 'GUIDE':
            login(request, user)
            return redirect('guide_dashboard') # Ensure this URL name exists
        messages.error(request, "Invalid credentials or not a Guide.")
    return render(request, 'accounts/login_guide.html')

def team_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user and user.role == 'TEAM':
            login(request, user)
            return redirect('team_dashboard')
        messages.error(request, "Invalid credentials or not a Student Team.")
    return render(request, 'accounts/team_login.html')

@login_required
def team_dashboard(request):
    # Ensure only logged-in teams can see this
    if not request.user.is_authenticated or request.user.role != 'TEAM':
        return redirect('team_login')

    # FIX: Using 'student_profile' prevents the 'RelatedManager' attribute error
    try:
        team = request.user.student_profile
    except Team.DoesNotExist:
        messages.error(request, "Team profile not found. Please contact the Coordinator.")
        return redirect('team_login')

    # Accessing members from the specific team instance
    members = team.members.all()
    
    # Coordinator-controlled: Only show slots they have activated
    active_slots = DocumentSlot.objects.filter(is_active=True).order_by('deadline')
    
    # Get existing submissions for this specific team
    submissions = TeamSubmission.objects.filter(team=team)
    submitted_slots = submissions.values_list('slot_id', flat=True)

    context = {
        'team': team,
        'members': members,
        'guide': team.guide,
        'active_slots': active_slots,
        'submissions': submissions,
        'submitted_slots': submitted_slots, # Required for 'Submitted' status labels
    }
    return render(request, 'accounts/team_dashboard.html', context)

def upload_document(request, slot_id):
    if request.method == 'POST' and request.FILES.get('doc_file'):
        slot = DocumentSlot.objects.get(id=slot_id)
        # Status is handled automatically by the save() method in models.py
        TeamSubmission.objects.create(
            team=request.user.student_profile,
            slot=slot,
            file=request.FILES['doc_file']
        )
        messages.success(request, f"File for {slot.title} uploaded successfully.")
    return redirect('team_dashboard')

@login_required
def coordinator_dashboard(request):
    if request.user.role != 'COORDINATOR':
        return redirect('coordinator_login')

    teams = Team.objects.all().prefetch_related('members').order_by('-created_at')
    
    # 1. Fetch slots and create a map for easy lookup
    slots = DocumentSlot.objects.all()
    slots_dict = {slot.slot_type: slot for slot in DocumentSlot.objects.all()}

    # 2. FEATURE: Map submissions by team with file URLs for viewing
    from collections import defaultdict
    submissions_raw = TeamSubmission.objects.all().select_related('slot')
    team_submissions_map = defaultdict(dict)
    for sub in submissions_raw:
        # Store the URL so the badge becomes a clickable link
        team_submissions_map[sub.team_id][sub.slot.slot_type] = sub.file.url 

    # --- MAINTAINED: EXCEL EXPORT ---
    if 'export_excel' in request.GET:
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=Team_Master_Sheet.xlsx'
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Team Details"
        ws.append(['Team ID', 'Project Title', 'Guide', 'Members (Reg No)'])
        for team in teams:
            member_list = ", ".join([f"{m.name} ({m.reg_number})" for m in team.members.all()])
            ws.append([team.team_id, team.project_title or "Not Set", str(team.guide), member_list])
        wb.save(response)
        return response

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_title':
            team = get_object_or_404(Team, pk=request.POST.get('team_id'))
            team.project_title = request.POST.get('project_title')
            team.is_approved = True 
            team.save()
            return redirect('coordinator_dashboard')

        elif action == 'edit_title':
            team = get_object_or_404(Team, pk=request.POST.get('team_id'))
            team.is_approved = False 
            team.save()
            return redirect('coordinator_dashboard')

        elif action == 'set_deadline':
            slot_type = request.POST.get('slot_type')
            notification_msg = ""
            
            if slot_type in ['REV1', 'REV2', 'PPT1', 'PPT2']: # Added PPT options
                date_val = request.POST.get('review_date') or request.POST.get('specific_review_date')
                label = slot_type # Uses the code as label
                DocumentSlot.objects.update_or_create(
                    slot_type=slot_type,
                    defaults={'title': f"{label} Presentation", 'review_date': date_val, 'is_active': True, 'deadline': None}
                )
                notification_msg = f"{label} date sent and teams notified."
            else:
                date_val = request.POST.get('deadline_date')
                titles = {'PROPOSAL': 'Project Proposal', 'ABSTRACT': 'Abstract', 'SRS': 'SRS Document', 'REPORT': 'Final Report'}
                title = titles.get(slot_type, "Document Submission")
                DocumentSlot.objects.update_or_create(
                    slot_type=slot_type,
                    defaults={'title': title, 'deadline': date_val, 'is_active': True, 'review_date': None}
                )
                notification_msg = "Deadline sent and teams notified."

            # Broadcast Notification
            student_emails = User.objects.filter(role='TEAM').values_list('email', flat=True)
            try:
                send_mail(
                    subject=f"EvalX Update: {slot_type}",
                    message=f"Hello Teams,\n\n{notification_msg}\n\nPlease check your dashboard.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=list(student_emails),
                    fail_silently=False,
                )
                messages.success(request, notification_msg)
            except Exception:
                messages.warning(request, f"{notification_msg} (Email notifications failed).")

            return redirect('coordinator_dashboard')
        
        elif action == 'delete_deadline':
            slot_type = request.POST.get('slot_type')
            # Fetch the slot for this specific type
            slot = DocumentSlot.objects.filter(slot_type=slot_type).first()
            
            if slot:
                slot_title = slot.title
                slot.delete()
                messages.success(request, f"Successfully deleted the deadline for: {slot_title}")
            else:
                messages.error(request, "Error: Could not find a deadline for that category.")
            
            return redirect('coordinator_dashboard')

    context = {
        'teams': teams,
        'slots_dict': slots_dict,
        'team_submissions_map': dict(team_submissions_map),
        'now': timezone.now(), # Required for overdue (RED) check
        'members': TeamMember.objects.all().order_by('reg_number'),
    }
    return render(request, 'accounts/coordinator_dashboard.html', context)

@login_required
def evaluate_r1_batch_coordinator(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.method == 'POST':
        for m in members:
            m.r1_c_comp = float(request.POST.get(f'comp_{m.id}', 0))
            m.r1_c_func = float(request.POST.get(f'func_{m.id}', 0))
            m.r1_c_pres = float(request.POST.get(f'pres_{m.id}', 0))
            m.r1_c_oral = float(request.POST.get(f'oral_{m.id}', 0))
            m.r1_c_know = float(request.POST.get(f'know_{m.id}', 0))
            m.r1_c_absent = f'absent_{m.id}' in request.POST
            m.save()
        return redirect('coordinator_dashboard')
    return render(request, 'accounts/batch_sheet_r1.html', {'members': members})

@login_required
def evaluate_r2_batch_coordinator(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.method == 'POST':
        for m in members:
            m.r2_c_comp = float(request.POST.get(f'comp_{m.id}', 0))
            m.r2_c_func = float(request.POST.get(f'func_{m.id}', 0))
            m.r2_c_pres = float(request.POST.get(f'pres_{m.id}', 0))
            m.r2_c_oral = float(request.POST.get(f'oral_{m.id}', 0))
            m.r2_c_know = float(request.POST.get(f'know_{m.id}', 0))
            m.r2_c_absent = f'absent_{m.id}' in request.POST
            m.save()
        return redirect('coordinator_dashboard')
    return render(request, 'accounts/batch_sheet_r2.html', {'members': members})

@login_required
def evaluate_s2_batch_coordinator(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.method == 'POST':
        for m in members:
            m.s2_teamwork = float(request.POST.get(f'teamwork_{m.id}', 0))
            m.s2_tech_know = float(request.POST.get(f'tech_{m.id}', 0))
            m.s2_regularity = float(request.POST.get(f'reg_{m.id}', 0))
            m.save()
        messages.success(request, "Institutional Sheet 2 updated.")
        return redirect('coordinator_dashboard')
    return render(request, 'accounts/batch_sheet_s2.html', {'members': members})

@login_required
def evaluate_report_batch_coordinator(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.method == 'POST':
        for m in members:
            m.report_coord = float(request.POST.get(f'report_{m.id}', 0))
            m.save()
        return redirect('coordinator_dashboard')
    return render(request, 'accounts/batch_sheet_report.html', {'members': members})

@login_required
def evaluate_attendance_batch_coordinator(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.method == 'POST':
        for m in members:
            m.attendance_marks = float(request.POST.get(f'attendance_{m.id}', 0))
            m.save()
        return redirect('coordinator_dashboard')
    return render(request, 'accounts/batch_sheet_attendance.html', {'members': members})

# --- REUSABLE EXCEL HELPER ---

def export_to_excel(queryset, filename, sheet_name, headers, row_callback):
    """Generates an Excel response using openpyxl."""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # Add Bold Headers
    ws.append(headers)
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)
    
    for obj in queryset:
        ws.append(row_callback(obj))
        
    wb.save(response)
    return response

# --- CONSOLIDATED PDF & EXCEL REPORTS ---

def generate_branded_pdf(template_src, context_dict, filename):
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'branding', 'logo.png')
    context_dict['logo_path'] = logo_path
    html = render_to_string(template_src, context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

@login_required
def report_r1_consolidated(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.GET.get('format') == 'excel':
        return export_to_excel(members, "R1_Consolidated", "Review 1", 
                              ['Reg No', 'Name', 'Guide', 'HOD', 'Coord', 'Total (40)'],
                              lambda m: [m.reg_number, m.name, m.r1_guide_total, m.r1_hod_total, m.r1_coord_total, m.r1_consolidated_40])
    return generate_branded_pdf('accounts/pdf_r1_cons.html', {'members': members, 'title': 'REVIEW 1 CONSOLIDATED'}, 'R1_Consolidated')

@login_required
def report_r2_consolidated(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.GET.get('format') == 'excel':
        return export_to_excel(members, "R2_Consolidated", "Review 2", 
                              ['Reg No', 'Name', 'Guide', 'HOD', 'Coord', 'Total (40)'],
                              lambda m: [m.reg_number, m.name, m.r2_guide_total, m.r2_hod_total, m.r2_coord_total, m.r2_consolidated_40])
    return generate_branded_pdf('accounts/pdf_r2_cons.html', {'members': members, 'title': 'REVIEW 2 CONSOLIDATED'}, 'R2_Consolidated')

@login_required
def report_avg_evaluation_consolidated(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.GET.get('format') == 'excel':
        return export_to_excel(members, "Avg_Evaluation", "Average Eval", 
                              ['Reg No', 'Name', 'R1 Cons', 'R2 Cons', 'Avg (40)'],
                              lambda m: [m.reg_number, m.name, m.r1_consolidated_40, m.r2_consolidated_40, m.avg_evaluation_40])
    return generate_branded_pdf('accounts/pdf_avg_eval_cons.html', {'members': members, 'title': 'AVERAGE EVALUATION (40)'}, 'Avg_Evaluation')

@login_required
def report_report_marks_consolidated(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.GET.get('format') == 'excel':
        return export_to_excel(members, "Report_Marks", "Report Marks", 
                              ['Reg No', 'Name', 'Guide', 'HOD', 'Coord', 'Consolidated (10)'],
                              lambda m: [m.reg_number, m.name, m.report_guide, m.report_hod, m.report_coord, m.consolidated_report_marks])
    return generate_branded_pdf('accounts/pdf_report_cons.html', {'members': members, 'title': 'REPORT MARKS CONSOLIDATED'}, 'Report_Marks')

@login_required
def report_final_internal(request):
    members = TeamMember.objects.all().order_by('reg_number')
    if request.GET.get('format') == 'excel':
        return export_to_excel(members, "Final_Internal_75", "Final Internal", 
                              ['Reg No', 'Name', 'Avg Eval', 'Sheet 2', 'Report', 'Attend', 'Final (75)'],
                              lambda m: [m.reg_number, m.name, m.avg_evaluation_40, m.s2_total, m.consolidated_report_marks, m.attendance_marks, m.final_internal_75])
    return generate_branded_pdf('accounts/pdf_final_internal.html', {'members': members, 'title': 'FINAL INTERNAL MARKS (75)'}, 'Final_Internal_75')

@login_required
def report_team_master_pdf(request):
    if request.user.role != 'COORDINATOR':
        return redirect('coordinator_login')
    teams = Team.objects.all().prefetch_related('members').select_related('guide').order_by('team_id')
    
    if request.GET.get('format') == 'excel':
        # Custom logic for Team Master because it uses 'teams' instead of 'members'
        return export_to_excel(teams, "Team_Master_Record", "Teams", 
                              ['Team ID', 'Project Title', 'Guide', 'Members Details'],
                              lambda t: [t.team_id, t.project_title or "Not Set", str(t.guide), ", ".join([f"{m.name} ({m.reg_number})" for m in t.members.all()])])
        
    return generate_branded_pdf('accounts/pdf_master_sheet.html', {'teams': teams, 'title': 'OFFICIAL TEAM MASTER RECORD'}, 'Team_Master_Sheet')

def logout_view(request):
    """Clears the session and redirects to the landing page."""
    from django.contrib.auth import logout
    logout(request)
    return redirect('portal_gatekeeper')

@login_required
def hod_dashboard(request):
    if request.user.role != 'HOD':
        return redirect('hod_login')
    
    # Fetch all registered teams with their members
    teams = Team.objects.all().prefetch_related('members').order_by('team_id')
    
    return render(request, 'accounts/hod_dashboard.html', {'teams': teams})


@login_required
def guide_dashboard(request):
    if request.user.role != 'GUIDE':
        return redirect('guide_login')
    assigned_teams = Team.objects.filter(guide=request.user).prefetch_related('members')
    
    return render(request, 'accounts/guide_dashboard.html', {'teams': assigned_teams})