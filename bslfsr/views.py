from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Beneficiary, FarmerRecord, PeaceActivity
@login_required
def livelihood_dashboard(request):
    beneficiaries=Beneficiary.objects.filter(active=True)
    reach={}
    for category in ("girl","boy","woman","man"):
        for population in ("host","refugee"):
            qs=beneficiaries.filter(participant_category=category,displacement_status=population)
            reach[f"{category}_{population}"]=qs.count()
            reach[f"{category}_{population}_farmers"]=FarmerRecord.objects.filter(beneficiary__in=qs).values("beneficiary").distinct().count()
    return render(request,"bslfsr/livelihood_dashboard.html",{"beneficiaries":beneficiaries.count(),"farmers":FarmerRecord.objects.values("beneficiary").distinct().count(),"peace_activities":PeaceActivity.objects.count(),**reach})
