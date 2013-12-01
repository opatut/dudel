function get_slug(s) {
    s = s.replace(/[\s+]+/g, '-');
    s = s.replace(/[^a-zA-Z0-9_-]+/g, '');
    s = s.replace(/-+/g, '-');
    s = s.toLowerCase();
    return s;
}

function updateCheckbox(e) {
    $(this).closest(".checkbox-cell").removeClass("no yes maybe").addClass($(this).prop("checked") ? "yes" : "no");
}

$(document).ready(function() {
    $("[data-slug-field]").on("input", function() {
        var val = $(this).val();
        var slug = get_slug(val);
        var slug_input = $($(this).attr("data-slug-field"));
        slug_input.val(slug);
    });

    $(".checkbox-cell :checkbox").on("click", updateCheckbox).on("click", function(e) {
        e.stopPropagation();
    });

    $(".checkbox-cell").on("click", function(e){
        var checkbox = $(this).find(":checkbox");
        checkbox.prop("checked", !checkbox.prop("checked"));
        updateCheckbox.call(checkbox);
    });

    // initialize
    $(".checkbox-cell :checkbox").each(updateCheckbox);

    $(".calendar").each(function() {
        initCalendar($(this));
    });
    $("#date-form").hide();

    $(".script-only").css("display", "inline-block");

    $("#password_level").change(function() {
        $("#password").attr("disabled", $(this).val() == "0");
    });
    $("#password").attr("disabled", $("#password_level").val() == "0");

    $("td .vote-choice-radio").parent().hide();
    $("input[value='no'").attr("checked", "checked");
    $("td.vote-choice.control.no").removeClass("off");
    $(".vote-comment input").hide();
    $(".vote-comment span").click(function(e) {
        $(e.target).hide();
        $(e.target).parent().addClass("not-padded").find("input").show();
    });

    $("td.vote-choice").click(highlightVoteChoice);

    initTimeSlider();

    $(".toggle").click(function() {
        // deselect or select
        var selected = $(this).hasClass("toggle-select");
        var cells;
        if($(this).hasClass("toggle-column")) {
            var index = $(this).closest("td").index() + 1;
            cells = $(this).closest("table").find("tr td:nth-child(" + index + ")");
        } else if($(this).hasClass("toggle-row")) {
            cells = $(this).closest("tr").find("td");
        } else {
            cells = $(this).closest("table").find("td");
        }
        updateCheckbox.call(cells.find(":checkbox").prop("checked", selected));
    });

    $(".time-remove-button").click(function() {
        var split = $(this).val().split(":");
        $("#time-hour").val(split[0]);
        $("#time-minute").val(split[1]);
        $("#time-slider-form").submit();
    });
});

$.fn.rotate = function(degrees) {
    $(this).css({
  '-webkit-transform' : 'rotate('+degrees+'deg)',
     '-moz-transform' : 'rotate('+degrees+'deg)',
      '-ms-transform' : 'rotate('+degrees+'deg)',
       '-o-transform' : 'rotate('+degrees+'deg)',
          'transform' : 'rotate('+degrees+'deg)',
               'zoom' : 1

    });
};

/* Time Slider */

function initTimeSlider() {
    $("#time-slider").click(sliderPosition).mousemove(function(e) {
        if(e.which == 1) sliderPosition.call(this, e);
    });
    $("#time-minute, #time-hour").keyup(function() {
        var hour = $("#time-hour").val();
        var minute = $("#time-minute").val();
        if(!hour || !minute) return;
        setSliderPosition( parseInt(hour), parseInt(minute), true);
    }).focus(function(e) {
        $(this).select();
    }).mouseup(function(e) {
        e.preventDefault();
    });
    setSliderPosition(12, 0);

    // suppress initial animation
    setTimeout(function() {
        $(".time-slider-display .hour, .time-slider-display .minute").addClass("animated");
    }, 100);
}

function sliderPosition(e) {
    var offset = 8;
    var width = 384;
    var progress = (e.pageX - offset - $(this).offset().left) / width;
    progress = Math.min(1, Math.max(0, progress));
    var steps = 24 * 4;
    var step = Math.round(steps*progress);
    var hour = Math.floor(step/4);
    var minute = 15 * (step % 4);
    setSliderPosition(hour, minute);
}

function setSliderPosition(_hour, _minute, suppressValueUpdate) {
    var hour = (_hour + (_minute-(_minute%60))/60) % 24;
    // alert(hour + " // " + _hour);
    var minute = _minute % 60;

    var steps = 24 * 4 + 1;
    var offset = 8;
    var width = 384;

    var step = hour * 4 + minute/15;
    var pos = (step / (steps-1)) * width + offset;
    // $("#time-debug").text(step/4);
    $("#time-slider-knob").css("left", pos);

    $(".time-slider-display .hour").rotate(hour / 12 * 360 + minute / 60 / 12 * 360);
    $(".time-slider-display .minute").rotate(hour * 360 + minute / 60 * 360);

    if(!suppressValueUpdate || hour!=_hour || minute!=_minute) {
        $("#time-hour").val(hour);
        $("#time-minute").val(minute < 10 ? "0" + minute : minute);
    }
}

/* Vote choices */

function highlightVoteChoice(event) {
    var $target = $(event.target);
    var $parent = $(event.target).parent();
    if ($(event.target).prop("tagName") == "SPAN") {
        $target = $parent;
        $parent = $parent.parent();
    }
    $parent.find("td.vote-choice.control").addClass("off");
    $target.removeClass("off");
    $parent.find("input").prop("checked", false);
    $parent.find("input[value='" + $target.data("choice") + "']").prop("checked", true);
}

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
