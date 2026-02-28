from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.portal_gatekeeper, name='portal_gatekeeper'),
    path('register/', views.register_team, name='register_team'),
    path('login/coordinator/', views.coordinator_login, name='coordinator_login'),
    path('login/hod/', views.hod_login, name='hod_login'),
    path('login/guide/', views.guide_login, name='guide_login'),
    path('login/team/', views.team_login, name='team_login'),
    path('dashboard/team/', views.team_dashboard, name='team_dashboard'),
    path('upload/<int:slot_id>/', views.upload_document, name='upload_document'),
    path('logout/', auth_views.LogoutView.as_view(next_page='portal_gatekeeper'), name='logout'),
    path('coordinator/dashboard/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('guide/dashboard/', views.guide_dashboard, name='guide_dashboard'),
    path('reports/master-sheet-pdf/', views.report_team_master_pdf, name='report_master_sheet_pdf'),
    # --- COORDINATOR BATCH ENTRY PATHS ---
    # Note: No <int:member_id> here because these handle the whole batch
    path('coordinator/batch/r1/', views.evaluate_r1_batch_coordinator, name='batch_r1_coordinator'),
    path('coordinator/batch/r2/', views.evaluate_r2_batch_coordinator, name='batch_r2_coordinator'),
    path('coordinator/batch/s2/', views.evaluate_s2_batch_coordinator, name='batch_s2_coordinator'),
    path('coordinator/batch/report/', views.evaluate_report_batch_coordinator, name='batch_report_coordinator'),
    path('coordinator/batch/attendance/', views.evaluate_attendance_batch_coordinator, name='batch_attendance_coordinator'),

    # --- CONSOLIDATED REPORT PATHS (PDF) ---
    path('reports/r1-consolidated/', views.report_r1_consolidated, name='report_r1_cons'),
    path('reports/r2-consolidated/', views.report_r2_consolidated, name='report_r2_cons'),
    path('reports/avg-evaluation/', views.report_avg_evaluation_consolidated, name='report_avg_eval'),
    path('reports/report-marks/', views.report_report_marks_consolidated, name='report_report_cons'),
    path('reports/final-internal/', views.report_final_internal, name='report_final_internal'),
    path('reports/master-sheet-pdf/', views.report_team_master_pdf, name='report_master_sheet_pdf'),
]