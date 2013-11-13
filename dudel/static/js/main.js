function get_slug(s) {
    s = s.replace(/[\s+]+/g, '-');
    s = s.replace(/[^a-zA-Z0-9_-]+/g, '');
    s = s.replace(/-+/g, '-');
    s = s.toLowerCase();
    return s;
}

$(document).ready(function() {
    $("[data-slug-field]").on("input", function() {
        var val = $(this).val();
        var slug = get_slug(val);
        var slug_input = $($(this).attr("data-slug-field"));
        slug_input.val(slug);
    });

    $(".checkbox-cell").on("click", function() {
        $(this).find(":checkbox").each(function() {
            $(this).click();
            $(this).closest(".checkbox-cell").removeClass("no yes maybe").addClass($(this).prop("checked") ? "yes" : "no");
            //$(this).prop("checked", !$(this).prop("checked"));
        });
    });

    $(".checkbox-cell :checkbox").on("click", function(e){
        $(this).closest(".checkbox-cell").removeClass("no yes maybe").addClass($(this).prop("checked") ? "yes" : "no");
        e.stopPropagation();
    });

    $(".checkbox-cell :checkbox").each(function(e){
        $(this).closest(".checkbox-cell").removeClass("no yes maybe").addClass($(this).prop("checked") ? "yes" : "no");
    });

    $(".calendar").each(function() {
        initCalendar($(this));
    });
    $("#date-form").hide();

    $(".script-only").css("display", "inline-block");
});


function initCalendar(calendar) {
    var date = CURRENT_DATE ? moment(CURRENT_DATE) : moment();
    setDate(calendar, date);

    calendar.find(".next-month").click(function() {
        setDate(calendar, calendar.data("date").add("months", 1));
    });
    calendar.find(".prev-month").click(function() {
        setDate(calendar, calendar.data("date").subtract("months", 1));
    });

    calendar.on("click", "button.day", function() {
        var date = calendar.data("date");
        date.date($(this).text());
        var datetime = date.format("YYYY-MM-DD");
        $(calendar.attr("data-calendar-field")).val(datetime).closest("form").submit();
    });
}

function setDate(calendar, date) {
    date = date.startOf("month"); // first day of the month
    calendar.data("date", date);
    updateMonth(calendar);
}

function updateMonth(calendar) {
    var date = calendar.data("date");

    calendar.find(".title").text(date.format("MMMM YYYY"));
    calendar.find(".week").remove();

    var week = [];
    var start = date.isoWeekday();
    var endDay = date.endOf("month").date();
    var end = Math.ceil( (endDay + start) / 7 ) * 7;
    for(var i = 1; i <= end; ++i) {
        var day = i - start;
        week.push(day >= 0 && day < endDay ? day+1 : 0);
        if(i%7 == 0) {
            makeWeek(calendar, week);
            week = [];
        }
    }
}

function makeWeek(calendar, week) {
    var tr = $('<tr class="week"></tr>');
    for(var i = 0; i < 7; ++i) {
        var btn = "";
        if(week[i] != 0) {
            var date = calendar.data("date");
            date.date(week[i]);
            var datetime = date.format("YYYY-MM-DD");
            // alert(datetime);
            var enabled = (ENABLED_DATES.indexOf(datetime) !== -1);
            var past = date.isBefore(moment());
            var t = (past && !enabled ? 'span' : 'button');
            btn = '<' + t + ' class="day btn-xs ' + (enabled ? 'btn btn-success' : (past ? '' : 'btn btn-default')) + '">' + week[i] + '</' + t + '>';
        }
        tr.append($('<td>' + btn + '</td>'));
    }
    calendar.find("table").append(tr);
}
