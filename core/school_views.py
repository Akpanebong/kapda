from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render
from .models import School


@login_required
def school_list(request):
    query = request.GET.get("q", "").strip()
    schools = School.objects.select_related("location").annotate(
        learner_total=Count("enrolments__learner", distinct=True)
    ).order_by("name")
    if query:
        schools = schools.filter(Q(name__icontains=query) | Q(school_code__icontains=query) | Q(location__district__icontains=query))
    return render(request, "core/school_list.html", {
        "schools": Paginator(schools, 25).get_page(request.GET.get("page")),
        "query": query,
    })
