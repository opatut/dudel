from dudel import app, ICONS

@app.template_filter()
def date(s):
    return s.strftime("%a %d %b")

@app.template_filter()
def time(s):
    return s.strftime("%H:%M")

@app.context_processor
def inject():
    return dict(
        ICONS=ICONS
        )

