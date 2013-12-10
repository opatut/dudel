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
    $("td .vote-choice-radio").parent().hide();
    $(".vote-comment .vote-choice-comment").hide();
    $(".vote-choice-edit").click(showComment);
    $(".vote-choice-edit-all").click(function() {
        $(".vote-choice-edit").each(function(i) {
            var t = $(this);
            setTimeout(function() {
                showComment.call(t);
            }, i * 150);
        });
    });

    $(".vote-choice-column").click(function() {
        $('.vote-choice.control[data-choice="' + $(this).data("choice") + '"].off').click();
    });

    $("td.vote-choice").click(highlightVoteChoice);

    $("[data-toggle='tooltip']").tooltip();

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

function highlightVoteChoice(event) {
    var is_off = $(this).hasClass("off");

    var tr = $(this).closest("tr");
    tr.find("td.vote-choice.control").addClass("off");
    tr.find("input").prop("checked", false);

    if(is_off) {
        $(this).removeClass("off");
        if(is_off) tr.find("input[value='" + $(this).data("choice") + "']").prop("checked", true);
    }
}
