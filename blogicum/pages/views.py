from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.template import engines

def csrf_failure(request, reason='', exception=None):
    """Обработчик ошибки CSRF токена и общий обработчик 403 ошибок."""
    try:
        return render(request, 'pages/403csrf.html', status=403)
    except Exception:
        # Fallback для случаев, когда render не может работать с простым HttpRequest
        # (например, в тестах без полного middleware stack)
        django_engine = engines['django']
        template = django_engine.get_template('pages/403csrf.html')
        try:
            html = template.render({}, request)
        except Exception:
            # Если и это не работает, возвращаем простой ответ
            html = '<h1>Ошибка CSRF токена. 403</h1>'
        return HttpResponse(html, status=403)


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    return render(request, 'pages/500.html', status=500)


# CBV для статических страниц (требование задания)
class AboutView(TemplateView):
    template_name = 'pages/about.html'


class RulesView(TemplateView):
    template_name = 'pages/rules.html'