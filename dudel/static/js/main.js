$(document).ready(function() {
    $("[data-slug-field]").on("input", function() {
        var val = $(this).val();
        var slug = get_slug(val);
        var slug_input = $($(this).attr("data-slug-field"));
        slug_input.val(slug);
    });

    $(".script-only").css("display", "block");
    $("td.script-only").css("display", "table-cell");
    $("tr.script-only").css("display", "table-row");
    $("table.script-only").css("display", "table");

    // $("#password_level").change(function() {
    //     $("#password").attr("disabled", $(this).val() == "0");
    // });
    // $("#password").attr("disabled", $("#password_level").val() == "0");

    // Voting

    // Hide voting radio column
    $("td .vote-choice-radio").parent().hide();

    // Apply checked radio states to table cells
    $(".vote-choice-radio input:checked").each(function() {
        $(this).closest("tr").find("[data-choice=\"" + $(this).val() + "\"]").removeClass("off");
    })

    // Buttons: "Show comment field"
    $(".vote-choice-edit").click(showComment);

    // Button: "Show all comment fields"
    $(".vote-choice-edit-all").click(function() {
        $(".vote-choice-edit").each(function(i) {
            var t = $(this);
            setTimeout(function() {
                showComment.call(t);
            }, i * 50);
        });
    });

    // Hide comment fields, but show those that do have input
    $(".vote-comment .vote-choice-comment").hide();
    $(".vote-comment input[value!=\"\"]").each(function() {
        showComment.call($(this).closest(".vote-comment").find(".vote-choice-edit"));
    });

    // Button: "all" (selecting the whole column)
    $(".vote-choice-column").click(function() {
        $('.vote-choice.control[data-choice="' + $(this).data("choice") + '"].off').click();
    });
    
    // Fast selecting of voting cells
    var fastselectState = {'active': false}
    $("td.vote-choice").mousedown(function() {
        fastselectState.active = true;
        $('table.vote').disableSelect();
        highlightVoteChoice($(this));
        $('body').one('mouseup', function() {
            fastselectState.active = false;
            $('table.vote').enableSelect();
        });
    }).mouseenter(function() {
        if(fastselectState.active) {
            highlightVoteChoice($(this));
        }
    });

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

    $("#due_date").datetimepicker({
        dateFormat: "yy-mm-dd",
        timeFormat: "HH:mm",
        stepMinute: 15,
    });

    $("[data-toggle='tooltip']").tooltip();

    $(".icon-preview button").click(function() {
        $("#icon").val($(this).data("icon"));
    }).each(function() {
        $(this).find("span").text(ICONS[$(this).data("icon")]).hide();
    }).css("width", "28px");

    $("#color").colorpicker({
        "buttonClass": "btn"
    });

    // Comment positioning
    // Relative positioning is not defined on elements with
    // display:table-cell. Therefore we wrap everything in a div
	// with position:relative and emulate table cell properties.
    // (see http://www.w3.org/TR/CSS21/visuren.html#choose-position)
    $('td.vote-choice:has(span.comment-icon)').each(function() {
        var cell = $(this);
        var cellHeight = cell.outerHeight() + 'px';
        var div = $('<div></div>').css({
            'position': 'relative',
            'padding': cell.css('padding'),
            'width': '100%',
            'height': cellHeight,
            'line-height': cellHeight
        });
        cell.css('padding', 0).wrapInner(div);
        cell.find('span.comment-icon').css('display', 'block');
    });
});

/* Vote choices */

function showComment() {
    $(this).hide().closest("td").find("input")
        .css("width", 0).show()
        .animate({
            width: "100%"
        }, 400, "easeOutQuart");
    return false;
}

function highlightVoteChoice(elem) {
    var is_off = elem.hasClass("off");

    var tr = elem.closest("tr");
    tr.find("td.vote-choice.control").addClass("off");
    tr.find("input").prop("checked", false);

    if(is_off) {
        elem.removeClass("off");
        if(is_off) tr.find("input[value='" + elem.data("choice") + "']").prop("checked", true);
    }
}
