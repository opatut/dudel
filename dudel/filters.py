from dudel import app

@app.template_filter()
def date(s):
    return s.strftime("%a %d %b")

@app.template_filter()
def time(s):
    return s.strftime("%H:%M")

