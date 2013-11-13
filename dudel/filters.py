from dudel import app

@app.template_filter()
def date(s):
    return s.strftime("%d %B, %Y")

@app.template_filter()
def time(s):
    return s.strftime("%H:%M")

