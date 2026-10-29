from django.contrib.auth.decorators import login_required
from accounts.access import record_editor_required
from .crud_support import create_record, delete_record, detail_record, list_records, update_record
from .models import AcademicYear, Household, Location, School, Term

@login_required
def school_list(request): return list_records(request, School, "core/school_list.html", "schools")
@login_required
@record_editor_required
def school_create(request): return create_record(request, School, "core/school_form.html", "data:school_list")
@login_required
@record_editor_required
def school_update(request, pk): return update_record(request, School, pk, "core/school_form.html", "data:school_list")
@login_required
@record_editor_required
def school_delete(request, pk): return delete_record(request, School, pk, "data:school_list")

@login_required
def location_list(request): return list_records(request, Location, "core/location_list.html", "locations")
@login_required
def location_detail(request, pk): return detail_record(request, Location, pk, "core/location_detail.html")
@login_required
@record_editor_required
def location_create(request): return create_record(request, Location, "core/location_form.html", "data:location_list")
@login_required
@record_editor_required
def location_update(request, pk): return update_record(request, Location, pk, "core/location_form.html", "data:location_list")
@login_required
@record_editor_required
def location_delete(request, pk): return delete_record(request, Location, pk, "data:location_list")

@login_required
def household_list(request): return list_records(request, Household, "core/household_list.html", "households")
@login_required
def household_detail(request, pk): return detail_record(request, Household, pk, "core/household_detail.html")


@login_required
@record_editor_required
def household_create(request):
    return create_record(request, Household, "core/household_form.html",
                         "data:household_list")


@login_required
@record_editor_required
def household_update(request, pk): return update_record(request, Household, pk, "core/household_form.html", "data:household_list")
@login_required
@record_editor_required
def household_delete(request, pk): return delete_record(request, Household, pk, "data:household_list")

@login_required
def academic_year_list(request): return list_records(request, AcademicYear, "core/academic_year_list.html", "academic_years")
@login_required
def academic_year_detail(request, pk): return detail_record(request, AcademicYear, pk, "core/academic_year_detail.html")
@login_required
@record_editor_required
def academic_year_create(request): return create_record(request, AcademicYear, "core/academic_year_form.html", "data:academic_year_list")
@login_required
@record_editor_required
def academic_year_update(request, pk): return update_record(request, AcademicYear, pk, "core/academic_year_form.html", "data:academic_year_list")
@login_required
@record_editor_required
def academic_year_delete(request, pk): return delete_record(request, AcademicYear, pk, "data:academic_year_list")

@login_required
def term_list(request): return list_records(request, Term, "core/term_list.html", "terms")
@login_required
def term_detail(request, pk): return detail_record(request, Term, pk, "core/term_detail.html")
@login_required
@record_editor_required
def term_create(request): return create_record(request, Term, "core/term_form.html", "data:term_list")
@login_required
@record_editor_required
def term_update(request, pk): return update_record(request, Term, pk, "core/term_form.html", "data:term_list")
@login_required
@record_editor_required
def term_delete(request, pk): return delete_record(request, Term, pk, "data:term_list")
