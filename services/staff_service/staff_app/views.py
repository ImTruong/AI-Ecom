from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'staff-service'})

@csrf_exempt
def staff_login(request):
    # Dummy login for initialization check
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Staff login logic not implemented yet'})
    return JsonResponse({'error': 'POST required'}, status=405)
