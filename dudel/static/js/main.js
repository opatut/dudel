function makeRandomString(length) {
    var text = "";
    var possible = "ABCDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz0123456789";

    for(var i=0; i < length; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }

    return text;
}

function slugField() {
    var field = $("[data-slug-field]");
    if(field.length == 0) return;
    var val = field.val();
    var slug = get_slug(val);
    var slug_input = $(field.attr("data-slug-field"));

    if($("#randomize-slug").is(":checked")) {
        slug = makeRandomString(8);
    }

    slug_input.val(slug);
}

$(document).ready(function() {
    $("#randomize-slug").on("click", slugField);
    $("[data-slug-field]").on("input", slugField);
    slugField();

    $(".script-only").css("display", "block");
    $("td.script-only").css("display", "table-cell");
    $("tr.script-only").css("display", "table-row");
    $("table.script-only").css("display", "table");

    $('[data-toggle="popover"]').popover({
        html: true,
        container: 'body',
        trigger: 'hover'
    });

    // $("#password_level").change(function() {
    //     $("#password").attr("disabled", $(this).val() == "0");
    // });
    // $("#password").attr("disabled", $("#password_level").val() == "0");

    // Voting

    // Hide voting radio column
    $("td .vote-choice-radio").parent().hide();

    // Apply checked radio states to table cells
    $(".vote-choice-radio:checked").each(function() {
        $(this).closest("tr").find("[data-choice=\"" + $(this).val() + "\"]").removeClass("off");
    });

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
        var choice = $(this).data("choice");
        $('.vote-choice[data-choice="' + choice + '"]').each(function() {
            setChoiceByCell(this);
        });
    });

    // Fast selecting of voting cells
    var draggingMouse = false;
    var draggingStartCell = null;
    $("td.vote-choice").mousedown(function() {
        draggingMouse = true;
        draggingStartCell = this;
        $('table.vote').disableSelect();

        // set starting choice
        if($(this).hasClass("off")) {
            setChoiceByCell(this);
        } else {
            resetChoiceByCell(this);
        }

        $('body').on('mouseup', function() {
            draggingMouse = false;
            $('table.vote').enableSelect();
        });
    }).mouseenter(function() {
        // set starting choice
        if(draggingMouse) {
            if(draggingStartCell) {
                setChoiceByCell(draggingStartCell);
                draggingStartCell = null;
            }
            setChoiceByCell(this);
        }
    });

    $(".vote-choice-radio").change(function() {
        setChoice($(this).parents("tr").data("vote-choice"), $(this).val());
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

    $("select.make-button-group").each(function() {
        var select = $(this);
        select.hide();

        var group = $('<div class="btn-group input-group"></div>');
        select.after(group);

        select.find("option").each(function() {
            var option = $(this);
            var button = $('<button type="button" class="btn btn-sm btn-default"></button>');
            button.text(option.text());
            button.val(option.val());
            button.click(function() {
                group.find(".btn").removeClass("active");
                button.addClass("active");
                select.val(button.val());
                return false;
            });
            group.append(button);
        });

        group.find(".btn[value='" + select.val() + "']").addClass("active");
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

function setChoiceByCell(cell) {
    setChoice($(cell).parents("tr").data("vote-choice"), $(cell).data("choice"));
}

function resetChoiceByCell(cell) {
    setChoice($(cell).parents("tr").data("vote-choice"), 0);
}

function setChoice(voteChoice, choice) {
    console.log(voteChoice, choice);
    var tr = $('[data-vote-choice="' + voteChoice + '"]');
    tr.find('input[type="radio"]').prop("checked", false);
    tr.find('input[type="radio"][value="' + choice + '"]').prop("checked", true);
    tr.find('td.vote-choice').addClass("off");
    tr.find('td.vote-choice[data-choice="' + choice + '"]').removeClass("off");
}
