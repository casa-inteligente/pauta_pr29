# middleware.py
from django.http import HttpResponseForbidden

ALLOWED_IPS = ['10.40.22.0/24']
BLOCKED_IPS = ['10.40.22.43']  # Adicione e remova IPs conforme necessário

class RestrictIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        #print(f"Request IP: {ip}")  # Adicione esta linha para depuração
        if self.is_blocked(ip):
            #print(f"Blocked IP: {ip}")  # Adicione esta linha para depuração
            return HttpResponseForbidden("ACESSO PROIBIDO")
        if not self.is_allowed(ip):
            return HttpResponseForbidden("ACESSO PROIBIDO")
        response = self.get_response(request)
        return response

    def is_allowed(self, ip):
        import ipaddress
        for allowed_ip in ALLOWED_IPS:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(allowed_ip):
                return True
        return False

    def is_blocked(self, ip):
        return ip in BLOCKED_IPS
