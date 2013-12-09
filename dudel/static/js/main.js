$(document).ready(function() {
    $("[data-slug-field]").on("input", function() {
        var val = $(this).val();
        var slug = get_slug(val);
        var slug_input = $($(this).attr("data-slug-field"));
        slug_input.val(slug);
    });

    $(".script-only").css("display", "block");

    // $("#password_level").change(function() {
    //     $("#password").attr("disabled", $(this).val() == "0");
    // });
    // $("#password").attr("disabled", $("#password_level").val() == "0");

    // Voting
    $("td .vote-choice-radio").parent().hide();
    $("input[value='no']").attr("checked", "checked");
    $("td.vote-choice.control.no").removeClass("off");
    $(".vote-comment .vote-choice-radio").hide();
    $(".vote-comment .vote-choice-comment").hide();
    $(".vote-comment .vote-choice-edit").click(function(e) {
        $(e.target).hide();
        $(e.target).parent().addClass("not-padded").find("input").show();
        return false;
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
