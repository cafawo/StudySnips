from django.shortcuts import render, redirect
from .forms import SnipForm
from .models import Classroom, Snip
import random
# API specific imports
from django.http import JsonResponse
from django.utils.html import format_html
from django.db.models import Count, DateField
from django.db.models.functions import TruncDate

def ordinal_format(n):
    """
    Convert an integer into its ordinal representation.

    :param n: Integer to convert.
    :return: Ordinal number as a string.
    """
    return "%d%s" % (n, "th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

def home(request):
    message = None  # Initialize message variable
    initial_data = {}

    # Check if there's a snip_id in the GET request and use it to pre-populate the form
    snip_id = request.GET.get('snip_id')
    if snip_id:
        initial_data['snip_id'] = snip_id  # Add the snip_id to the form's initial data

    if request.method == 'POST':
        form = SnipForm(request.POST)
        if form.is_valid():
            snip_id = form.cleaned_data['snip_id']
            student_id = form.cleaned_data['student_id']
            try:
                snip = Snip.objects.get(snip_id=snip_id)
                leaderboard_url = f'/leaderboard/?classroom={snip.snipsheet.classroom.classroom_id}'
                snip.claim_attempts += 1
                if snip.student_id:
                    message = 'Nice try, but this Snip has already been claimed. 😑'
                    form = SnipForm()  # Reset form
                else:
                    snip.student_id = student_id
                    # Access the classroom through the snip's snipsheet
                    classroom = snip.snipsheet.classroom
                    # Count how many Snips the student has in this classroom
                    previously_claimed_snips = Snip.objects.filter(snipsheet__classroom=classroom, student_id=student_id).count()
                    # Select emoji for this message
                    emoji = random.choice(['🎉', '👏', '🎈', '🥳', '😎', '🙌'])
                    # Update the success message to include the ordinal number and random emoji
                    message = f'Awesome, you have successfully claimed your {ordinal_format(previously_claimed_snips + 1)} Snip! {emoji}'
                    form = SnipForm()  # Reset form
                snip.save()
            except Snip.DoesNotExist:
                message = 'Sorry, this Snip does not exist. ☹️'
    else:
        # Initialize the form with GET data if present, or with no data if not
        form = SnipForm(initial=initial_data)

    context = {
        'form': form,
        'message': message,
        'leaderboard_url': leaderboard_url,
    }
    return render(request, 'snips/home.html', context)

# API
def api_chart_data(request):
    # Filter the Snips where student_id is not empty or null, then group by date
    data = (Snip.objects
                .filter(student_id__isnull=False, student_id__gt='')
                .annotate(date=TruncDate('updated_at'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date'))
    # Format the data for the chart (date in 'YYYY-MM-DD' format and the count)
    chart_data = [{'date': entry['date'].isoformat(), 'count': entry['count']} for entry in data]
    return JsonResponse(chart_data, safe=False)

# Chart
def chart_page(request):
    return render(request, 'snips/chart.html')


def leaderboard(request):
    classroom_id = request.GET.get('classroom') or request.GET.get('classroom_id')
    leaderboard_rows = []
    error_message = None

    if not classroom_id:
        error_message = 'Please provide a classroom id using ?classroom=...'
    else:
        classroom_exists = Classroom.objects.filter(classroom_id=classroom_id).exists()
        if not classroom_exists:
            error_message = 'Classroom not found.'
        else:
            leaderboard_rows = list(
                Snip.objects.filter(
                    snipsheet__classroom__classroom_id=classroom_id,
                    student_id__isnull=False,
                )
                .exclude(student_id='')
                .values('student_id')
                .annotate(snip_count=Count('id'))
                .order_by('-snip_count', 'student_id')[:10]
            )

    for idx, row in enumerate(leaderboard_rows, start=1):
        row['place'] = str(idx)

    context = {
        'classroom_id': classroom_id,
        'leaderboard_rows': leaderboard_rows,
        'error_message': error_message,
    }
    return render(request, 'snips/leaderboard.html', context)
